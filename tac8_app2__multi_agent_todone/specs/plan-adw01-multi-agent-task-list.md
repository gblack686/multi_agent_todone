# Plan: Multi-Agent Task List Architecture

## Metadata
adw_id: `adw01`
prompt: `# Specification

We're building a multi-agent task list architecture that wraps a primary application layer.
There are two main components:
- Agentic Layer (.claude/commands + adws/*)
- Application Layer (apps/*)

The idea here is simple. We update a task list, which a cron file picks up which then we kick off agents to do the work. Agents operate in groups on their own git worktrees.
When the agents complete work or fail, they update the task list. We leverage the agentic layer of our codebase .claude/* and adws/* to build out the agents and workflows.
Below our additional details.

## Setup

Before starting your work run the following commands
- Read and execute .claude/commands/prime.md to understand the codebase.
- Read and understand the structure of all .claude/commands/*.md prompt files. When we create new files in this directory we're going to write prompts in this format for our agents to use.

## Key Files
> some exists and some are new, track which need to be created as you build out the new plan.

- tasks.md - this is the task list that is used to track the state of the tasks. human engineers and agents will update this file.
- .claude/commands/ - this is where we'll store our prompts that we'll use for the steps in the process
- adws/adw_triggers/adw_trigger_cron_todone.py - this is a cron job that runs every 5 (N seconds configurable) seconds and checks for tasks that are ready to be picked up by an agent. It does the following
  - It runs the /process_tasks command to get a list of tasks to pick up. 
  - Creates unique adw_ids for each. 
  - Immediately updates the task list and marks the tasks as [🟡 <adw_id>] work in progress so the next cron run does not pick up the same task again with the adw id attached. 
  - Then it if this is the first time a task is being picked up, we'll create a work tree /.claude/commands/init_worktree.md.
  - Then it will delegate each task to the adws/adw_plan_implement_update_task.py workflow one at a time - spinning up one instance per task.
- .claude/commands/plan.md - this is a template prompt that creates a plan for a task that gets called in the adws/adw_plan_implement_update_task.py workflow as the first step. (already built)
- .claude/commands/implement.md - this is a template prompt that implements the plan for a task that gets called in the adws/adw_plan_implement_update_task.py workflow as the second step. (already built)
- .claude/commands/init_worktree.md - this is a template prompt that creates a git work tree in the trees/<worktree_name> directory. It is used to initialize a work tree when a task is picked up for the first time. Note we'll also need to copy over .env to make sure the agent has everything they need to get running.
- adws/adw_modules/data_models.py - use this to define data models for the work we're going to do throughout this process. Use pydantic.
- .claude/commands/process_tasks.md - this reads in the current state of the task list and decides which tasks to pick up by returning a list of tasks top to bottom as a json array. The agent will immediately update the list and mark the tasks as [🟡] work in progress so the next cron run does not pick up the same task again. (kicked off by cron job with a template command /process_tasks). Note, we cannot process blocked tasks [⏰], until the tasks above them are completed. Note, this task only determines what needs to be done, it does not do the work or update the task list at all. This is the object structure that is returned.
  ```json
  [
    {
      worktree_name: "worktree_name",
      tasks_to_start: [{
        description: "task description",
        tags: ["tag1", "tag2", "tag3"]
      }]
    }
  ]
  ```
- adws/adw_plan_implement_update_task.py - this ai developer workflow will run three templates prompts: /plan, /implement, /update_task. see adws/adw_chore_implement.py to understand how to build a multi-agent workflow. note make sure we pass the adw_id and the worktree_name to the workflow and use the path to the worktree as the working directory for every prompt that runs, this is critical.
- .claude/commands/update_task.md - this updates the task list based on individual agents response as the last step of the adws/adw_plan_implement_update_task.py and marks work as [✅] success or [❌] failed. These states mark the end of a task (kicked off by agent doing work, at the end their work will call). This specifically updates the task list with the adw_id and the commit hash.


## Task state machine

Simple state machine to understand the flow of task states and how updates them.

```pseudo-mermaid
stateDiagram-v2

    <!-- human engineer creates a task -->
    start --> []
    start --> [⏰]
    
    <!-- our cron agent picks these up and processes them  -->
    [] --> [🟡]
    [⏰] --> [🟡]
    
    [🟡] --> [✅]
    [🟡] --> [❌]
    
    [✅] --> end
    [❌] --> end
```


## Details

- ToDone - multi-agent-task-list - MATL 
- One task represents a unit of engineering work that will result in one commit
- Agents only perform a single task at a time and are only focused on that task.
- We have a cron job that runs every 5 seconds that checks for 
- adw_trigger_cron_todone.py only acts on [] and [⏰] tasks. And only on [⏰] tasks that have ONLY have success tasks above them. These are blocking tasks.
- Statuses:
  - [✅] success - the work has been completed and committed
  - [🟡] work in progress - an agent has picked up the task and is working on it
  - [❌] failed - the agent failed to complete the task and has stopped working on it
  - [] not started - this task is ready to be picked up by an agent
  - [⏰] not started and blocked - This task cannot be started until all tasks above it are completed

## Example tasks.md file

```md

# ATL

## Git Worktree <name the worktree>
[✅ <commit_hash>, <adw_id>] <description>
[🟡, <adw_id>] <description>
[❌, <adw_id>] <description>
[] <description> {tag}
[⏰] <description>
[] <description>

## Git Worktree <name the worktree>
[✅ <commit_hash>, <adw_id>] <description>
[🟡, <adw_id>] <description>
[❌, <adw_id>] <description>
[] <description>
[⏰] <description>

...
```
`
task_type: feature
complexity: complex

## Task Description
Build a multi-agent task list architecture that enables autonomous agents to pick up, process, and complete engineering tasks from a shared task list. The system will use git worktrees to isolate agent work, a cron job to orchestrate task distribution, and a state machine to track task progress. Agents will execute tasks through a three-phase workflow (plan, implement, update) and update the task list with their results.

## Objective
Create a fully functional multi-agent task management system where:
- Human engineers can add tasks to a markdown-based task list
- A cron job automatically distributes tasks to agents
- Agents work in isolated git worktrees to prevent conflicts
- Tasks progress through a defined state machine with clear status indicators
- The system automatically tracks task completion and failures

## Problem Statement
Currently, there's no automated system to distribute and track engineering tasks across multiple autonomous agents. This makes it difficult to:
- Parallelize development work across multiple agents
- Track the state and progress of multiple concurrent tasks
- Ensure agents don't conflict with each other's work
- Maintain a clear audit trail of what work was done by which agent

## Solution Approach
Build a task orchestration system with:
1. A markdown-based task list (`tasks.md`) that serves as the central task queue
2. Slash command templates that define agent behaviors for processing tasks
3. A cron job that monitors the task list and dispatches work to agents
4. Git worktrees to isolate each agent's work environment
5. A multi-phase workflow (plan → implement → update) for task execution
6. Pydantic data models to ensure type safety across the system

## Relevant Files
Use these files to complete the task:

- `deep_docs/uv_single_file_scripts.md` - uv single file scripts guide
- `README.md` - Project overview to understand the agentic and application layers
- `adws/README.md` - ADW architecture documentation for building workflows
- `.claude/commands/plan.md` - Existing planning template (reference)
- `.claude/commands/implement.md` - Existing implementation template (reference)
- `.claude/commands/chore.md` - Example slash command template structure
- `adws/adw_chore_implement.py` - Reference implementation of multi-agent workflow
- `adws/adw_modules/agent.py` - Core agent execution module
- `adws/adw_triggers/adw_trigger_cron_todone.py` - Existing cron trigger to modify (uv single file script)

### New Files
- `tasks.md` - Central task list file
- `.claude/commands/process_tasks.md` - Template to analyze and select tasks
- `.claude/commands/init_worktree.md` - Template to create git worktrees
- `.claude/commands/update_task.md` - Template to update task status
- `adws/adw_modules/data_models.py` - Pydantic models for the system
- `adws/adw_plan_implement_update_task.py` - Three-phase workflow executor (uv single file script)

## Implementation Phases

### Phase 1: Foundation
Create the core data models and basic task list structure:
- Define Pydantic models for tasks, worktrees, and workflow states
- Create initial `tasks.md` with example structure
- Build the `/process_tasks` command template

### Phase 2: Core Implementation
Build the main workflow components:
- Create `/init_worktree` and `/update_task` command templates
- Implement the three-phase workflow executor
- Modify the cron trigger to orchestrate task distribution

### Phase 3: Integration & Polish
Connect all components and add robustness:
- Test the complete workflow end-to-end
- Add error handling and recovery mechanisms
- Create documentation and usage examples

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### 1. Define Data Models
- Create comprehensive Pydantic models in `adws/adw_modules/data_models.py`
- Define `Task`, `Worktree`, `ProcessTasksResponse`, and `TaskUpdate` models
- Include proper validation and documentation for each field

### 2. Create Task List File
- Create `tasks.md` with the specified markdown structure
- Add example worktrees and tasks demonstrating all status types
- Include proper formatting with status indicators and metadata

### 3. Build Process Tasks Command
- Create `.claude/commands/process_tasks.md` template
- Implement logic to parse task list and identify eligible tasks
- Return structured JSON response with worktree groupings
- Handle blocked task detection based on upstream task status

### 4. Create Worktree Initialization Command
- Create `.claude/commands/init_worktree.md` template
- Implement git worktree creation in `trees/<worktree_name>` directory
- Copy `.env` file to new worktree for agent configuration
- Set up proper branch naming and initial commit

### 5. Build Task Update Command
- Create `.claude/commands/update_task.md` template
- Implement task status updates with proper metadata (adw_id, commit hash)
- Handle both success and failure scenarios
- Preserve task list formatting and structure

### 6. Implement Three-Phase Workflow
- Create `adws/adw_plan_implement_update_task.py` based on `adw_chore_implement.py`
- Add parameters for adw_id and worktree_name
- Configure working directory to use worktree path for all commands
- Chain `/plan`, `/implement`, and `/update_task` commands

### 7. Modify Cron Trigger
- Update `adws/adw_triggers/adw_trigger_cron_todone.py`
- Add logic to call `/process_tasks` command
- Generate unique adw_ids for each task
- Update task statuses to [🟡] before delegation
- Check for first-time worktree creation needs
- Delegate to `adw_plan_implement_update_task.py` workflow

### 8. Add Error Handling
- Implement proper exception handling in all components
- Add retry logic for transient failures
- Ensure task list updates are atomic to prevent corruption
- Log all operations for debugging

### 9. Create Integration Tests
- Write test scenarios for different task configurations
- Test blocked task handling
- Verify worktree isolation
- Test failure scenarios and recovery

### 10. Validate Complete System
- Run end-to-end test with multiple tasks
- Verify agents work in isolation
- Check task state transitions
- Ensure proper git commits are created

## Testing Strategy
1. **Unit Tests**: Test individual components (data models, parsers, status updates)
2. **Integration Tests**: Test workflow chains and command interactions
3. **System Tests**: Full end-to-end testing with multiple concurrent agents
4. **Edge Cases**:
   - Simultaneous task pickup attempts
   - Task list corruption recovery
   - Worktree creation failures
   - Network/API failures during execution

## Acceptance Criteria
- [ ] `tasks.md` can be parsed and updated reliably
- [ ] Cron job correctly identifies and distributes eligible tasks
- [ ] Agents successfully create and work in isolated git worktrees
- [ ] Task states transition correctly through the state machine
- [ ] Multiple agents can work concurrently without conflicts
- [ ] Failed tasks are properly marked and don't block the system
- [ ] Successful tasks include commit hashes in their status
- [ ] System recovers gracefully from failures

## Validation Commands
Execute these commands to validate the task is complete:

- `python -m py_compile adws/adw_modules/data_models.py` - Verify data models compile
- `python -m py_compile adws/adw_plan_implement_update_task.py` - Verify workflow compiles
- `python -m py_compile adws/adw_triggers/adw_trigger_cron_todone.py` - Verify cron trigger compiles
- `ls -la trees/` - Verify worktree directory structure
- `cat tasks.md` - Verify task list format and content
- `./adws/adw_triggers/adw_trigger_cron_todone.py --dry-run` - Test cron job in dry-run mode

## Notes
- Build the trigger file and the plan implement update as a uv single file script.
- Ensure all file paths use absolute paths when working with worktrees
- The cron job should have configurable polling interval (default 5 seconds)
- Consider using file locking for `tasks.md` updates to prevent race conditions
- Git worktrees require git 2.5.0 or higher