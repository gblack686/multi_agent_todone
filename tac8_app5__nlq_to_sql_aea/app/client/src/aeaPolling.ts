import type { AEAAgent, AEAMessage } from './types';

/**
 * Polling manager class for vanilla TypeScript
 * Handles real-time updates for AEA chat windows
 */
export class AEAPollingService {
  private agentId: string;
  private intervalId: number | null = null;
  private abortController: AbortController | null = null;
  private pollInterval = 1500; // 1.5 seconds
  private lastMessageCount = 0;
  private currentAgent: AEAAgent | null = null;
  
  // Store serialized state for comparison
  private lastAgentHash: string = '';
  
  // Track activity for intelligent polling
  private lastActivityTime: number = Date.now();
  private consecutiveNoChanges: number = 0;
  
  // Callbacks for UI updates
  private onAgentUpdate: (agent: AEAAgent) => void;
  private onError: (error: string) => void;
  private onStateChange: (oldState: string | null, newState: string) => void;
  private onNewMessage: (message: AEAMessage) => void;
  
  constructor(
    agentId: string,
    callbacks: {
      onAgentUpdate: (agent: AEAAgent) => void;
      onError: (error: string) => void;
      onStateChange: (oldState: string | null, newState: string) => void;
      onNewMessage: (message: AEAMessage) => void;
    }
  ) {
    this.agentId = agentId;
    this.onAgentUpdate = callbacks.onAgentUpdate;
    this.onError = callbacks.onError;
    this.onStateChange = callbacks.onStateChange;
    this.onNewMessage = callbacks.onNewMessage;
  }
  
  /**
   * Start polling
   */
  start(): void {
    if (this.intervalId) return; // Already polling
    
    // Initial poll
    this.poll();
    
    // Set up interval
    this.intervalId = window.setInterval(() => {
      this.poll();
    }, this.pollInterval);
  }
  
  /**
   * Stop polling
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
  }
  
  /**
   * Create a hash of agent state for comparison
   */
  private getAgentHash(agent: AEAAgent): string {
    // Create a fingerprint of the important agent properties
    const fingerprint = {
      state: agent.state,
      agent_name: agent.agent_name,  // Include name to detect when it's added
      conversationLength: agent.conversation.length,
      lastMessage: agent.conversation.length > 0 
        ? agent.conversation[agent.conversation.length - 1] 
        : null,
      archived: agent.archived,
      // Include updated_at to catch any backend changes
      updated_at: agent.updated_at
    };
    
    return JSON.stringify(fingerprint);
  }
  
  /**
   * Check if agent has actually changed
   */
  private hasAgentChanged(agent: AEAAgent): boolean {
    const currentHash = this.getAgentHash(agent);
    const changed = currentHash !== this.lastAgentHash;
    
    if (changed) {
      console.debug(`[AEA Polling] Agent ${this.agentId} changed - updating UI`);
      this.lastAgentHash = currentHash;
    } else {
      console.debug(`[AEA Polling] Agent ${this.agentId} unchanged - skipping UI update`);
    }
    
    return changed;
  }
  
  /**
   * Single poll operation
   */
  private async poll(): Promise<void> {
    try {
      // Create abort controller for this request
      this.abortController = new AbortController();
      
      const response = await fetch(
        `http://localhost:8743/aea/poll_agent_by_id?agent_id=${this.agentId}`,
        {
          signal: this.abortController.signal,
          headers: { 'Content-Type': 'application/json' }
        }
      );
      
      if (!response.ok) {
        throw new Error(`Poll failed: ${response.statusText}`);
      }
      
      const agent: AEAAgent = await response.json();
      
      // Check if anything has actually changed
      const hasChanges = this.hasAgentChanged(agent);
      
      if (hasChanges) {
        // Reset inactivity counter
        this.consecutiveNoChanges = 0;
        this.lastActivityTime = Date.now();
        
        // Check for new messages
        if (agent.conversation.length > this.lastMessageCount) {
          const newMessages = agent.conversation.slice(this.lastMessageCount);
          newMessages.forEach(msg => this.onNewMessage(msg));
        }
        
        // Check for state changes
        if (this.currentAgent && this.currentAgent.state !== agent.state) {
          this.onStateChange(this.currentAgent.state, agent.state);
          
          // Stop polling if archived
          if (agent.state === 'archived') {
            this.stop();
            return;
          }
        }
        
        // Update state
        this.lastMessageCount = agent.conversation.length;
        this.currentAgent = agent;
        
        // Only notify UI if there were actual changes
        this.onAgentUpdate(agent);
        
        // Adjust polling interval based on new state
        this.adjustPollingInterval(agent.state);
      } else {
        // No changes, but update our reference for next comparison
        this.currentAgent = agent;
        this.consecutiveNoChanges++;
        
        // Slow down polling if inactive for a while
        if (this.consecutiveNoChanges > 10 && agent.state === 'idle') {
          // After 10 polls with no changes (15 seconds), slow down
          this.adjustPollingInterval('stale');
        }
      }
      
    } catch (error: any) {
      // Ignore abort errors
      if (error.name !== 'AbortError') {
        this.onError(error.message || 'Polling failed');
      }
    }
  }
  
  /**
   * Intelligently adjust polling interval based on state and activity
   */
  private adjustPollingInterval(state: string): void {
    const intervals: { [key: string]: number } = {
      'working': 1000,     // 1 second - fast polling when agent is working
      'idle': 2500,        // 2.5 seconds - moderate polling when idle
      'errored': 5000,     // 5 seconds - slow polling on error
      'stale': 10000       // 10 seconds - very slow for inactive agents
    };
    
    const newInterval = intervals[state] || 3000;
    
    // Only restart polling if interval actually changed
    if (newInterval !== this.pollInterval) {
      console.debug(`[AEA Polling] Adjusting interval from ${this.pollInterval}ms to ${newInterval}ms (state: ${state})`);
      this.pollInterval = newInterval;
      
      // Restart polling with new interval
      if (this.intervalId) {
        this.stop();
        this.start();
      }
    }
  }
  
  /**
   * Public method to update interval (for backwards compatibility)
   */
  updateInterval(state: string): void {
    this.adjustPollingInterval(state);
  }
}