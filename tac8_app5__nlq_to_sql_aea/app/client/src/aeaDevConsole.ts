import { AEAWindowManager } from './aeaWindowManager';
import type { AEAServerStatus } from './types';

/**
 * Dev Console for AEA system
 * Activated with Cmd+P, handles commands like /aea, /list, /toggle-view, /close-all
 */
export class AEADevConsole {
  private isOpen = false;
  private container: HTMLElement;
  private inputField!: HTMLInputElement;
  private windowManager: AEAWindowManager;
  private commandHistory: string[] = [];
  private historyIndex = -1;
  private serverAvailable = false;
  
  constructor() {
    this.windowManager = new AEAWindowManager();
    this.container = this.createConsoleElement();
    this.setupKeyboardShortcut();
    this.checkServerStatus();
  }
  
  /**
   * Create the console DOM element
   */
  private createConsoleElement(): HTMLElement {
    const consoleDiv = document.createElement('div');
    consoleDiv.id = 'aea-dev-console';
    consoleDiv.className = 'dev-console';
    consoleDiv.style.cssText = `
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 500px;
      background: #1e1e1e;
      border: 2px solid #333;
      border-radius: 8px;
      padding: 20px;
      z-index: 10000;
      display: none;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    `;
    
    consoleDiv.innerHTML = `
      <div class="console-header" style="margin-bottom: 10px; color: #fff;">
        <h3 style="margin: 0;">AEA Dev Console</h3>
        <p style="margin: 5px 0; font-size: 12px; color: #888;">
          Commands: /aea (new agent), /list (restore agents), /toggle-view (toggle visibility), /close-all (close all)
        </p>
      </div>
      <div class="console-status" id="server-status" style="margin-bottom: 10px; font-size: 12px;"></div>
      <input 
        type="text" 
        id="console-input" 
        placeholder="Enter command..." 
        style="
          width: 100%;
          padding: 10px;
          background: #2d2d2d;
          border: 1px solid #444;
          color: #fff;
          border-radius: 4px;
          font-family: 'Courier New', monospace;
        "
      />
      <div class="console-hint" style="margin-top: 5px; font-size: 11px; color: #666;">
        Press ESC to close
      </div>
    `;
    
    document.body.appendChild(consoleDiv);
    
    // Get input field reference
    this.inputField = consoleDiv.querySelector('#console-input')!;
    
    // Setup event handlers
    this.setupEventHandlers();
    
    return consoleDiv;
  }
  
  /**
   * Setup keyboard shortcut (Cmd+P or Ctrl+P)
   */
  private setupKeyboardShortcut(): void {
    document.addEventListener('keydown', (e) => {
      // Check for Cmd+P (Mac) or Ctrl+P (Windows/Linux)
      if ((e.metaKey || e.ctrlKey) && e.key === 'p') {
        e.preventDefault();
        this.toggle();
      }
      
      // ESC to close
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });
  }
  
  /**
   * Setup console event handlers
   */
  private setupEventHandlers(): void {
    // Handle command submission
    this.inputField.addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        const command = this.inputField.value.trim();
        if (command) {
          await this.handleCommand(command);
          this.commandHistory.push(command);
          this.historyIndex = this.commandHistory.length;
          this.inputField.value = '';
        }
      }
      
      // Command history navigation
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (this.historyIndex > 0) {
          this.historyIndex--;
          this.inputField.value = this.commandHistory[this.historyIndex];
        }
      }
      
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (this.historyIndex < this.commandHistory.length - 1) {
          this.historyIndex++;
          this.inputField.value = this.commandHistory[this.historyIndex];
        } else {
          this.historyIndex = this.commandHistory.length;
          this.inputField.value = '';
        }
      }
    });
    
    // Click outside to close
    document.addEventListener('click', (e) => {
      if (this.isOpen && !this.container.contains(e.target as Node)) {
        this.close();
      }
    });
  }
  
  /**
   * Check if AEA server is available
   */
  private async checkServerStatus(): Promise<void> {
    try {
      const response = await fetch('http://localhost:8743/aea/check_server');
      if (response.ok) {
        const status: AEAServerStatus = await response.json();
        this.serverAvailable = status.running;
        this.updateServerStatus(true, status.version);
      } else {
        this.serverAvailable = false;
        this.updateServerStatus(false);
      }
    } catch (error) {
      this.serverAvailable = false;
      this.updateServerStatus(false);
    }
  }
  
  /**
   * Update server status display
   */
  private updateServerStatus(available: boolean, version?: string): void {
    const statusDiv = this.container.querySelector('#server-status') as HTMLElement;
    if (available) {
      statusDiv.innerHTML = `<span style="color: #4ade80;">✓ AEA Server Connected${version ? ` (v${version})` : ''}</span>`;
    } else {
      statusDiv.innerHTML = `<span style="color: #ef4444;">✗ AEA Server Not Available - Start with: scripts/aea_server_start.sh</span>`;
    }
  }
  
  /**
   * Handle console commands
   */
  private async handleCommand(command: string): Promise<void> {
    console.log(`Executing command: ${command}`);
    
    // Check server before executing commands
    if (!this.serverAvailable && command !== '/help') {
      await this.checkServerStatus();
      if (!this.serverAvailable) {
        alert('AEA Server is not running. Please start it with: scripts/aea_server_start.sh');
        return;
      }
    }
    
    switch (command.toLowerCase()) {
      case '/aea':
      case '/agent':
        // Create new agent window
        try {
          const agentId = await this.windowManager.createNewAgent();
          console.log(`Created new agent: ${agentId}`);
          this.close();
        } catch (error) {
          console.error('Failed to create agent:', error);
          alert('Failed to create agent. Check console for details.');
        }
        break;
        
      case '/list':
        // Fetch all active agents and open windows
        console.log('Fetching all active agents from server...');
        await this.windowManager.openAllActiveAgents();
        this.close();
        break;
        
      case '/toggle-view':
        // Toggle visibility of all windows
        this.windowManager.toggleVisibility();
        this.close();
        break;
        
      case '/close-all':
        // Close all agent windows (equivalent to clicking 'x' on each)
        this.windowManager.closeAll();
        console.log('Closed all agent windows');
        this.close();
        break;
        
      case '/help':
        alert(`AEA Dev Console Commands:
        
/aea or /agent - Create a new AI agent window
/list - Restore all active agent sessions
/toggle-view - Toggle visibility of all agent windows
/close-all - Close all agent windows and end sessions
/help - Show this help message

Press ESC to close the console`);
        break;
        
      default:
        console.log(`Unknown command: ${command}`);
        alert(`Unknown command: ${command}\nType /help for available commands`);
    }
  }
  
  /**
   * Toggle console visibility
   */
  public toggle(): void {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }
  
  /**
   * Open the console
   */
  public open(): void {
    this.isOpen = true;
    this.container.style.display = 'block';
    this.inputField.focus();
    this.checkServerStatus();
  }
  
  /**
   * Close the console
   */
  public close(): void {
    this.isOpen = false;
    this.container.style.display = 'none';
    this.inputField.value = '';
  }
}