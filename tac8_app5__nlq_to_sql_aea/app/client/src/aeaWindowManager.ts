import { AEAChatWindow } from './aeaChatWindow';
import type { AEANewAgentResponse } from './types';

/**
 * Window Manager for multiple concurrent AEA agents
 * Handles creating, positioning, and managing multiple chat windows
 */
export class AEAWindowManager {
  private activeWindows: Map<string, AEAChatWindow> = new Map();
  private windowContainer: HTMLElement;
  private zIndexCounter = 1000;
  private windowWidth = 400;  // Standard window width
  private windowHeight = 600; // Standard window height
  private windowGap = 10;     // Gap between windows
  
  constructor() {
    // Create container for all chat windows
    this.windowContainer = document.createElement('div');
    this.windowContainer.id = 'aea-windows-container';
    this.windowContainer.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      pointer-events: none;
      z-index: 9999;
    `;
    document.body.appendChild(this.windowContainer);
  }
  
  /**
   * Calculate optimal position for new window
   */
  private calculateWindowPosition(): { top: number; left: number } {
    const windowCount = this.activeWindows.size;
    const windowsPerRow = 4; // 4 windows per row before stacking
    
    // Calculate row and column
    const rowIndex = Math.floor(windowCount / windowsPerRow);
    const colIndex = windowCount % windowsPerRow;
    
    // Base positioning
    const baseLeft = 20; // Start 20px from left edge
    const baseTop = 50;  // Start 50px from top
    
    // Calculate position
    let left: number;
    let top: number;
    
    if (rowIndex === 0) {
      // First row: position windows left to right
      left = baseLeft + (colIndex * (this.windowWidth + this.windowGap));
      top = baseTop;
    } else {
      // Subsequent rows: stack with offset for visibility
      const stackOffset = 30; // 30px offset for stacking effect
      left = baseLeft + (colIndex * (this.windowWidth + this.windowGap)) + (rowIndex * stackOffset);
      top = baseTop + (rowIndex * (this.windowHeight / 2)); // Half height offset for each row
    }
    
    return { top, left };
  }
  
  /**
   * Create a new agent and open its chat window
   */
  async createNewAgent(): Promise<string> {
    try {
      // Create new agent via API
      const response = await fetch('http://localhost:8743/aea/new_agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      if (!response.ok) throw new Error('Failed to create agent');
      
      const data: AEANewAgentResponse = await response.json();
      const agent = data.agent;
      
      // Create window container with positioning
      const windowDiv = document.createElement('div');
      windowDiv.className = 'aea-window-wrapper';
      const position = this.calculateWindowPosition();
      windowDiv.style.cssText = `
        position: absolute;
        top: ${position.top}px;
        left: ${position.left}px;
        width: ${this.windowWidth}px;
        height: ${this.windowHeight}px;
        pointer-events: auto;
        z-index: ${this.zIndexCounter++};
      `;
      
      // Make draggable
      this.makeDraggable(windowDiv);
      
      // Create chat window
      const chatWindow = new AEAChatWindow(agent.agent_id, windowDiv);
      
      // Handle window close
      chatWindow.onClose = () => {
        this.activeWindows.delete(agent.agent_id);
      };
      
      // Store reference
      this.activeWindows.set(agent.agent_id, chatWindow);
      
      // Add to container
      this.windowContainer.appendChild(windowDiv);
      
      console.log(`Created new agent window: ${agent.agent_id}`);
      return agent.agent_id;
      
    } catch (error) {
      console.error('Failed to create new agent:', error);
      throw error;
    }
  }
  
  /**
   * Make a window draggable and clickable to bring to front
   */
  private makeDraggable(element: HTMLElement): void {
    let isDragging = false;
    let startX: number;
    let startY: number;
    let initialX: number;
    let initialY: number;
    
    // Add click handler to entire window to bring it to front
    element.addEventListener('mousedown', (e) => {
      // Bring window to front on any click within the window
      element.style.zIndex = String(this.zIndexCounter++);
    });
    
    // Wait for header to be created
    setTimeout(() => {
      const header = element.querySelector('.aea-header') as HTMLElement;
      if (!header) return;
      
      header.style.cursor = 'move';
      
      header.addEventListener('mousedown', (e) => {
        // Don't drag if clicking on close button
        if ((e.target as HTMLElement).classList.contains('aea-close')) {
          return;
        }
        
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        
        const rect = element.getBoundingClientRect();
        initialX = rect.left;
        initialY = rect.top;
        
        // Note: z-index already updated by the window-wide mousedown handler
        
        e.preventDefault();
      });
      
      document.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        
        const deltaX = e.clientX - startX;
        const deltaY = e.clientY - startY;
        
        element.style.left = `${initialX + deltaX}px`;
        element.style.top = `${initialY + deltaY}px`;
      });
      
      document.addEventListener('mouseup', () => {
        isDragging = false;
      });
    }, 100);
  }
  
  /**
   * Reconnect to existing agent (doesn't create new, just opens window)
   */
  async reconnectToAgent(agentId: string): Promise<void> {
    // Check if already open
    if (this.activeWindows.has(agentId)) {
      console.log(`Agent ${agentId} already has an open window`);
      // Bring to front
      const existingWindow = this.activeWindows.get(agentId);
      if (existingWindow) {
        const windowDiv = (existingWindow as any).container as HTMLElement;
        windowDiv.style.zIndex = String(this.zIndexCounter++);
      }
      return;
    }
    
    // Create window container with positioning
    const windowDiv = document.createElement('div');
    windowDiv.className = 'aea-window-wrapper';
    const position = this.calculateWindowPosition();
    windowDiv.style.cssText = `
      position: absolute;
      top: ${position.top}px;
      left: ${position.left}px;
      width: ${this.windowWidth}px;
      height: ${this.windowHeight}px;
      pointer-events: auto;
      z-index: ${this.zIndexCounter++};
    `;
    
    // Make draggable
    this.makeDraggable(windowDiv);
    
    // Create chat window for existing agent
    const chatWindow = new AEAChatWindow(agentId, windowDiv);
    
    // Handle window close
    chatWindow.onClose = () => {
      this.activeWindows.delete(agentId);
    };
    
    // Store reference
    this.activeWindows.set(agentId, chatWindow);
    
    // Add to container
    this.windowContainer.appendChild(windowDiv);
    
    console.log(`Reconnected to agent: ${agentId}`);
  }
  
  /**
   * Fetch all active agents from server and open windows
   */
  async openAllActiveAgents(): Promise<void> {
    try {
      // Fetch list of non-archived agent IDs from server
      const response = await fetch('http://localhost:8743/aea/get_agent_ids');
      
      if (!response.ok) {
        throw new Error('Failed to fetch active agents');
      }
      
      const agentIds: string[] = await response.json();
      
      console.log(`Found ${agentIds.length} active agents on server:`, agentIds);
      
      // Open window for each agent
      for (const agentId of agentIds) {
        await this.reconnectToAgent(agentId);
        // Small delay to prevent overwhelming the server
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      
      if (agentIds.length === 0) {
        console.log('No active agents found. Use /aea to create a new agent.');
      }
      
    } catch (error) {
      console.error('Failed to fetch active agents:', error);
    }
  }
  
  /**
   * Get locally open agent windows
   */
  getOpenWindowIds(): string[] {
    return Array.from(this.activeWindows.keys());
  }
  
  /**
   * Close all windows
   */
  closeAll(): void {
    this.activeWindows.forEach(window => window.close());
    this.activeWindows.clear();
  }
  
  /**
   * Hide/show all windows
   */
  toggleVisibility(): void {
    const isHidden = this.windowContainer.style.display === 'none';
    this.windowContainer.style.display = isHidden ? 'block' : 'none';
  }
}