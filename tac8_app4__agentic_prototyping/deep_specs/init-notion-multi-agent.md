# Notion-Based Multi-Agent Rapid Prototyping System

## Executive Summary

This document outlines the engineering plan for implementing a comprehensive notion-based multi-agent system that enables rapid prototyping and development workflow automation. The system will replace task file-based workflows with a dynamic Notion-driven approach, providing real-time task management, agent coordination, and live progress updates.

## System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Notion Pages   │    │   Cron Trigger  │    │  Agent Workflows│
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Task Pages  │ │◄──►│ │   Polling   │ │◄──►│ │Build Update │ │
│ │             │ │    │ │   Service   │ │    │ │             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │Live Updates │ │    │ │Task Parser  │ │    │ │Plan Impl Upd│ │
│ │             │ │    │ │             │ │    │ │             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Notion Integration Layer
- **Database**: Agentic Prototyper database (ID: `247fc382-ac73-8038-9bf6-f0727259e1a3`)
- **Task Properties**: Name, Status, Assign
- **Status Values**: Not started, In progress, Done, HIL Review, Failed
- **Content Parsing**: Extract task details from page content blocks

### 2. Polling Service (`adw_trigger_cron_notion_tasks.py`)
- **Frequency**: Every 15 seconds (configurable)
- **Responsibilities**:
  - Query Notion database for eligible tasks
  - Parse task content and extract execution triggers
  - Delegate tasks to appropriate workflows
  - Handle task state transitions

### 3. Agent Workflows
- **Build-Update**: `adws/adw_build_update_task.py` (lightweight, direct implementation)
- **Plan-Implement-Update**: `adws/adw_plan_implement_update_task.py` (full planning cycle)

### 4. Live Update System
- **Progress Tracking**: Write agent outputs to Notion pages as JSON blocks
- **Status Updates**: Real-time task status and completion notifications
- **Error Handling**: Capture and report failures with detailed context

## Data Models & Types

### Notion Task Models

```python
class NotionTask(BaseModel):
    """Represents a task from the Notion database."""
    
    page_id: str = Field(..., description="Notion page ID")
    title: str = Field(..., description="Task title/name") 
    status: Literal["Not started", "In progress", "Done", "HIL Review", "Failed"] = Field(
        ..., description="Current task status"
    )
    content_blocks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Page content blocks"
    )
    tags: Dict[str, str] = Field(
        default_factory=dict, description="Extracted tags from content {{key: value}}"
    )
    worktree: Optional[str] = Field(
        None, description="Target worktree name"
    )
    model: Optional[str] = Field(
        None, description="Claude model preference (opus/sonnet)"
    )
    workflow_type: Optional[str] = Field(
        None, description="Workflow to use (build/plan-implement)"
    )
    last_block_type: Optional[str] = Field(
        None, description="Type of the last content block"
    )
    execution_trigger: Optional[str] = Field(
        None, description="Execution command (execute/continue)"
    )

class NotionTaskUpdate(BaseModel):
    """Update payload for Notion task progress."""
    
    page_id: str = Field(..., description="Notion page ID to update")
    status: str = Field(..., description="New status value")
    content_blocks: List[Dict[str, Any]] = Field(
        default_factory=list, description="Content blocks to append"
    )
    agent_output: Optional[str] = Field(
        None, description="Agent output to add as JSON block"
    )

class WorktreeCreationRequest(BaseModel):
    """Request for automatic worktree creation."""
    
    task_description: str = Field(..., description="Task description for context")
    suggested_name: Optional[str] = Field(
        None, description="User-suggested worktree name"
    )
    base_branch: str = Field(
        default="main", description="Base branch for worktree"
    )

class NotionCronConfig(BaseModel):
    """Configuration for Notion-based cron trigger."""
    
    database_id: str = Field(..., description="Notion database ID")
    polling_interval: int = Field(
        default=15, ge=1, description="Polling interval in seconds"
    )
    max_concurrent_tasks: int = Field(
        default=3, ge=1, description="Maximum concurrent notion tasks"
    )
    default_model: str = Field(
        default="sonnet", description="Default Claude model"
    )
    apps_directory: str = Field(
        default="apps", description="Target apps directory"
    )
```

### Tag System

Tasks support a flexible tagging system using `{{key: value}}` syntax:

- `{{worktree: feature-auth}}` - Specify target worktree
- `{{model: opus}}` - Specify Claude model
- `{{workflow: plan}}` - Force plan-implement workflow
- `{{app: sentiment_analysis}}` - Target specific app directory

## Execution Flow

### 1. Task Discovery Phase

```python
def get_eligible_notion_tasks() -> List[NotionTask]:
    """
    Query Notion database for eligible tasks.
    
    Eligibility Criteria:
    - Status: "Not started" or "HIL Review"
    - Last content block starts with "execute" or "continue - <prompt>"
    - Not currently being processed by another agent
    """
    # Implementation flows through /get_notion_tasks command
```

### 2. Task Processing Phase

```python
def process_notion_task(task: NotionTask) -> None:
    """
    Process a single notion task through the appropriate workflow.
    
    Steps:
    1. Parse tags and determine configuration
    2. Ensure/create target worktree
    3. Update task status to "In progress"  
    4. Delegate to appropriate workflow
    5. Monitor and update progress
    """
```

### 3. Workflow Delegation

```python
def delegate_task(task: NotionTask) -> None:
    """
    Delegate task to appropriate workflow based on tags.
    
    Decision Logic:
    - If {{workflow: plan}} or complex task → plan-implement-update
    - Otherwise → build-update (lightweight)
    
    Model Selection:
    - {{model: opus}} → use Opus
    - {{model: sonnet}} → use Sonnet  
    - Default → Sonnet
    """
```

## Implementation Plan

### Phase 1: Core Infrastructure

#### 1.1 Update Data Models
- [ ] Add Notion-specific models to `adws/adw_modules/data_models.py`
- [ ] Extend SystemTag enum with Notion-specific tags
- [ ] Add validation for Notion page IDs and database references

#### 1.2 Create Worktree Auto-Generation
- [ ] Implement `/make_worktree_name` command in `.claude/commands/`
- [ ] Add logic to generate meaningful worktree names from task descriptions
- [ ] Integrate with existing `/init_worktree` workflow

#### 1.3 Update Notion Commands
- [ ] Enhance `get_notion_tasks.md` with eligibility filtering
- [ ] Update `update_notion_task.md` with new status values
- [ ] Enhance `update_notion_task_with_file.md` for JSON output blocks
- [ ] Add `move_notion_task.md` for status transitions

### Phase 2: Polling Service

#### 2.1 Rewrite Cron Trigger
- [ ] Replace task.md logic with Notion API calls in `adw_trigger_cron_notion_tasks.py`
- [ ] Implement notion task discovery and eligibility checking
- [ ] Add tag parsing and extraction logic
- [ ] Implement execution trigger detection ("execute"/"continue")

#### 2.2 Task State Management
- [ ] Implement task status transitions (Not started → In progress → Done/Failed)
- [ ] Add concurrency control to prevent duplicate task processing
- [ ] Implement task locking mechanism during processing

#### 2.3 Error Handling & Recovery
- [ ] Add robust error handling for Notion API failures
- [ ] Implement retry logic for transient failures
- [ ] Add dead letter queue for consistently failing tasks

### Phase 3: Workflow Integration

#### 3.1 Update Existing Workflows
- [ ] Modify `adw_build_update_task.py` to work with Notion task context
- [ ] Update `adw_plan_implement_update_task.py` for Notion integration
- [ ] Add Notion status updates throughout workflow execution

#### 3.2 Live Progress Updates
- [ ] Implement real-time progress updates to Notion pages
- [ ] Add JSON block formatting for agent outputs
- [ ] Create progress tracking blocks (start, progress, completion)

#### 3.3 Worktree Management
- [ ] Integrate automatic worktree creation with task processing
- [ ] Add worktree cleanup on task completion/failure
- [ ] Implement worktree naming conventions based on task context

### Phase 4: Advanced Features

#### 4.1 HIL (Human-in-the-Loop) Review
- [ ] Implement HIL Review status handling
- [ ] Add support for "continue - <prompt>" execution pattern
- [ ] Create review approval workflow

#### 4.2 Multi-App Support
- [ ] Add support for `{{app: name}}` tags
- [ ] Implement app-specific worktree creation
- [ ] Add app directory validation and setup

#### 4.3 Enhanced Monitoring
- [ ] Add comprehensive logging for all Notion operations
- [ ] Implement metrics collection for task processing times
- [ ] Create dashboard for monitoring agent activity

## File Structure Changes

```
├── adws/
│   ├── adw_triggers/
│   │   └── adw_trigger_cron_notion_tasks.py    # Updated for Notion
│   ├── adw_modules/
│   │   ├── data_models.py                      # Extended with Notion models
│   │   ├── notion_client.py                    # New: Notion API wrapper
│   │   └── worktree_manager.py                 # New: Automated worktree management
│   ├── adw_build_update_task.py               # Updated for Notion context
│   └── adw_plan_implement_update_task.py      # Updated for Notion context
├── .claude/commands/
│   ├── get_notion_tasks.md                    # Enhanced eligibility logic
│   ├── move_notion_task.md                    # Updated status transitions
│   ├── update_notion_task.md                  # Enhanced with new statuses
│   ├── update_notion_task_with_file.md        # JSON block formatting
│   └── make_worktree_name.md                  # New: Auto worktree naming
└── deep_specs/
    └── init-notion-multi-agent.md             # This document
```

## Command Updates Required

### `/get_notion_tasks` Enhancement

**Current Variables**: None specified
**New Variables**: 
- `database_id`: Target Notion database ID
- `status_filter`: Optional status filter (default: ["Not started", "HIL Review"])
- `limit`: Maximum tasks to return (default: 10)

**Enhanced Logic**:
1. Query Notion database with status filter
2. For each task, parse content blocks
3. Check for execution triggers in last block
4. Extract tags using `{{key: value}}` pattern
5. Return JSON array of eligible tasks

### `/update_notion_task_with_file` Enhancement  

**Current Variables**: Task ID, file path
**New Variables**:
- `page_id`: Notion page ID
- `agent_output_file`: Path to agent output JSON
- `block_type`: Type of block to create (code, callout, etc.)
- `status`: New task status (optional)

**Enhanced Logic**:
1. Read agent output from JSON file
2. Format as appropriate Notion block type
3. Append to page content
4. Update task status if provided
5. Add timestamp and agent metadata

### `/make_worktree_name` (New Command)

**Variables**:
- `task_description`: Full task description
- `app_context`: Optional app name context
- `prefix`: Optional prefix (default: "task")

**Logic**:
1. Extract key terms from task description
2. Generate meaningful, short name (max 20 chars)  
3. Ensure uniqueness against existing worktrees
4. Return formatted worktree name

**Examples**:
- "Implement user authentication for React app" → `task-user-auth`
- "Fix bug in sentiment analysis model" → `fix-sentiment-bug`
- "Add logging to payment service" → `add-payment-logs`

## Testing Strategy

### Unit Tests
- [ ] Test Notion API integration with mock responses
- [ ] Validate tag parsing logic with various input formats
- [ ] Test worktree name generation edge cases
- [ ] Verify task eligibility determination logic

### Integration Tests  
- [ ] End-to-end task processing with test Notion database
- [ ] Workflow delegation and execution paths
- [ ] Error handling and recovery scenarios
- [ ] Concurrent task processing behavior

### Performance Tests
- [ ] Notion API rate limiting and throttling
- [ ] Large task queue processing
- [ ] Memory usage during extended polling
- [ ] Worktree creation/cleanup performance

## Security Considerations

### Notion Access Control
- [ ] Implement proper API key management
- [ ] Validate database access permissions
- [ ] Add input sanitization for task content
- [ ] Implement audit logging for all Notion operations

### Code Execution Safety
- [ ] Sandbox worktree execution environments
- [ ] Validate generated code before execution
- [ ] Implement resource limits for agent processes
- [ ] Add monitoring for suspicious activity patterns

## Deployment Plan

### Development Phase
1. **Week 1-2**: Implement core data models and Notion integration
2. **Week 3-4**: Rewrite polling service and basic task processing
3. **Week 5-6**: Integration with existing workflows and testing
4. **Week 7-8**: Advanced features and production hardening

### Production Rollout
1. **Phase 1**: Deploy in parallel with existing task.md system
2. **Phase 2**: Migrate subset of tasks to Notion-based workflow
3. **Phase 3**: Full migration and deprecation of task.md system
4. **Phase 4**: Advanced features and optimization

## Monitoring & Observability

### Metrics to Track
- Task processing latency (discovery → completion)
- Notion API success/failure rates
- Agent workflow success rates by type
- Worktree creation/cleanup statistics
- Resource utilization (CPU, memory, disk)

### Alerting Thresholds
- Notion API failures > 5% over 5 minutes
- Task processing backlog > 10 items
- Agent workflow failures > 20% over 15 minutes
- Disk usage in worktrees > 80%

### Dashboards
- Real-time task processing status
- Agent performance and utilization
- Notion API health and rate limits
- Historical trends and analytics

## Risk Mitigation

### Technical Risks
- **Notion API Rate Limits**: Implement exponential backoff and request queuing
- **Database Schema Changes**: Version API calls and maintain backward compatibility  
- **Agent Process Failures**: Implement proper cleanup and recovery mechanisms
- **Worktree Disk Usage**: Automatic cleanup policies and monitoring

### Operational Risks
- **Task Content Parsing**: Robust error handling for malformed input
- **Concurrent Access**: Proper locking to prevent race conditions
- **Resource Exhaustion**: Limits on concurrent tasks and resource usage
- **Data Loss**: Regular backups of critical task state information

## Success Criteria

### Functional Requirements
- [ ] Successfully process 95%+ of eligible Notion tasks
- [ ] Real-time task status updates in Notion
- [ ] Automatic worktree creation and management
- [ ] Support for all defined tag types and workflows

### Performance Requirements
- [ ] Task discovery latency < 5 seconds
- [ ] End-to-end task processing < 5 minutes (simple tasks)
- [ ] Support for 10+ concurrent task processing
- [ ] 99.9% uptime for polling service

### Usability Requirements
- [ ] Intuitive task creation and management in Notion
- [ ] Clear progress visibility and error reporting
- [ ] Easy debugging and troubleshooting workflows
- [ ] Comprehensive documentation and examples

---

*This document serves as the engineering blueprint for implementing the Notion-based multi-agent rapid prototyping system. Regular updates will be made as implementation progresses and requirements evolve.*