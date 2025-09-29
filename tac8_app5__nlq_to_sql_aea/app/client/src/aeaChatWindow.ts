import { AEAPollingService } from './aeaPolling';
import type { AEAAgent, AEAMessage } from './types';

/**
 * AEA Chat Window component for vanilla TypeScript
 * Manages a single agent conversation window
 */
export class AEAChatWindow {
  private pollingService: AEAPollingService;
  private agent: AEAAgent | null = null;
  private container: HTMLElement;
  private messagesContainer!: HTMLElement;
  private inputField!: HTMLInputElement;
  private sendButton!: HTMLButtonElement;
  private statusIndicator!: HTMLElement;
  private agentId: string;
  
  // Callback for when window is closed
  public onClose?: () => void;
  
  constructor(agentId: string, container: HTMLElement) {
    this.agentId = agentId;
    this.container = container;
    this.initializeUI();
    
    // Set up polling - each window has its own polling service
    this.pollingService = new AEAPollingService(agentId, {
      onAgentUpdate: (agent) => this.handleAgentUpdate(agent),
      onError: (error) => this.handleError(error),
      onStateChange: (oldState, newState) => this.handleStateChange(oldState, newState),
      onNewMessage: (message) => this.handleNewMessage(message)
    });
    
    // Start polling
    this.pollingService.start();
  }
  
  private initializeUI(): void {
    this.container.innerHTML = `
      <div class="aea-chat-window">
        <div class="aea-header">
          <span class="aea-status-indicator" id="status"></span>
          <span class="aea-title" id="agent-title">AI Agent - Loading...</span>
          <button class="aea-close" id="close-btn">&times;</button>
        </div>
        <div class="aea-messages" id="messages"></div>
        <div class="aea-input-container">
          <input type="text" class="aea-input" id="input" placeholder="Type your message..." disabled />
          <button class="aea-send" id="send-btn" disabled>Query</button>
        </div>
      </div>
    `;
    
    this.messagesContainer = this.container.querySelector('#messages')!;
    this.inputField = this.container.querySelector('#input')!;
    this.sendButton = this.container.querySelector('#send-btn')! as HTMLButtonElement;
    this.statusIndicator = this.container.querySelector('#status')!;
    
    // Set up event listeners
    this.sendButton.addEventListener('click', () => this.sendMessage());
    
    this.inputField.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.sendMessage();
    });
    
    const closeBtn = this.container.querySelector('#close-btn')!;
    closeBtn.addEventListener('click', () => this.close());
  }
  
  private handleAgentUpdate(agent: AEAAgent): void {
    this.agent = agent;
    this.renderMessages();
    this.updateStatusIndicator(agent.state);
    
    // Update agent title with name if available, otherwise show agent ID
    const titleElement = this.container.querySelector('#agent-title') as HTMLElement;
    if (titleElement) {
      if (agent.agent_name) {
        titleElement.textContent = `AI Agent - ${agent.agent_name}`;
      } else {
        // Show agent ID while name is being generated
        titleElement.textContent = `AI Agent - ${agent.agent_id.substring(0, 8)}`;
      }
    }
    
    // Enable/disable input and send button based on state
    const isWorking = agent.state === 'working';
    this.inputField.disabled = isWorking;
    this.sendButton.disabled = isWorking;
    
    // Update button text to show status
    if (isWorking) {
      this.sendButton.textContent = 'Querying...';
    } else {
      this.sendButton.textContent = 'Query';
    }
    
    // Show error banner if errored
    if (agent.state === 'errored') {
      this.showErrorBanner();
    }
  }
  
  private handleError(error: string): void {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'aea-error-banner';
    errorDiv.textContent = `Error: ${error}`;
    this.messagesContainer.appendChild(errorDiv);
  }
  
  private handleStateChange(oldState: string | null, newState: string): void {
    console.log(`Agent state changed: ${oldState} -> ${newState}`);
    
    // Update polling interval based on new state
    this.pollingService.updateInterval(newState);
    
    // Re-enable input and send button if went from working to idle
    if (oldState === 'working' && newState === 'idle') {
      this.inputField.disabled = false;
      this.sendButton.disabled = false;
      this.sendButton.textContent = 'Query';
      this.inputField.focus();
    }
  }
  
  private handleNewMessage(message: AEAMessage): void {
    // Scroll to bottom
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    
    // Play notification sound if agent message
    if (message.who === 'agent') {
      this.playNotificationSound();
    }
  }
  
  private renderMessages(): void {
    if (!this.agent) return;
    
    this.messagesContainer.innerHTML = this.agent.conversation
      .map(msg => `
        <div class="aea-message aea-message-${msg.who}">
          <div class="aea-message-who">${msg.who === 'user' ? 'You' : (this.agent?.agent_name || 'Agent')}</div>
          <div class="aea-message-content">${this.escapeHtml(msg.content)}</div>
          <div class="aea-message-time">${new Date(msg.created).toLocaleTimeString()}</div>
        </div>
      `)
      .join('');
    
    // Auto-scroll to bottom after rendering messages
    this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
  }
  
  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  private updateStatusIndicator(state: string): void {
    this.statusIndicator.className = `aea-status-indicator aea-status-${state}`;
    this.statusIndicator.title = state;
  }
  
  private showErrorBanner(): void {
    const banner = document.createElement('div');
    banner.className = 'aea-error-banner';
    banner.innerHTML = `
      <span>⚠️ An error occurred</span>
      <button onclick="this.parentElement.remove()">Dismiss</button>
    `;
    this.messagesContainer.insertBefore(banner, this.messagesContainer.firstChild);
  }
  
  private playNotificationSound(): void {
    // Simple beep using Web Audio API
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      oscillator.frequency.value = 800;
      oscillator.type = 'sine';
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
      
      oscillator.start();
      oscillator.stop(audioContext.currentTime + 0.1);
    } catch (e) {
      // Audio not available
    }
  }
  
  private async sendMessage(): Promise<void> {
    const message = this.inputField.value.trim();
    if (!message || !this.agent || this.agent.state === 'working') return;
    
    // Immediately disable input and button to prevent double-send
    this.inputField.disabled = true;
    this.sendButton.disabled = true;
    this.sendButton.textContent = 'Querying...';
    
    try {
      const response = await fetch('http://localhost:8743/aea/prompt_agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: this.agent.agent_id,
          prompt: message
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to send message');
      }
      
      // Clear input
      this.inputField.value = '';
      
      // Note: The UI will be re-enabled when the agent state changes
      // via handleAgentUpdate or handleStateChange
      
    } catch (error: any) {
      this.handleError(error.message);
      
      // Re-enable on error
      this.inputField.disabled = false;
      this.sendButton.disabled = false;
      this.sendButton.textContent = 'Query';
    }
  }
  
  public async close(): Promise<void> {
    // Stop polling
    this.pollingService.stop();
    
    // End agent session
    if (this.agent) {
      try {
        await fetch('http://localhost:8743/aea/end_agent', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ agent_id: this.agent.agent_id })
        });
      } catch (e) {
        console.error('Failed to end agent session:', e);
      }
    }
    
    // Notify manager
    if (this.onClose) {
      this.onClose();
    }
    
    // Remove from DOM
    this.container.remove();
  }
}