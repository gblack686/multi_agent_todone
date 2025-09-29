# Multi Agent - Todone
> A multi-agent task delegation system for automated development workflows

## Overview

This system orchestrates multiple Claude Code agents to work on parallel development tasks across different git worktrees, automatically processing tasks from a central task list (`tasks.md`) and updating their status as work progresses.

## How It Works

### Task Management System

The system uses `tasks.md` to track development tasks organized by git worktree:

```markdown
## Git Worktree feature-auth
[] Task description                           # Pending task
[🟡, adw_12345] Task in progress              # Agent working (ADW ID tracked)
[✅ abc123, adw_12345] Completed task         # Success with commit hash
[❌, adw_12345] Failed task // Failed: Error  # Failed with error reason
[⏰] Blocked task                              # Waits for previous tasks
```

### Multi-Agent Workflow

1. **Cron Trigger** (`adw_triggers/adw_trigger_cron_todone.py`)
   - Scans `tasks.md` for pending tasks
   - Spawns parallel agents for different worktrees
   - Respects task dependencies and blocking

2. **Task Processing Workflows**
   - `adw_build_update_task.py` - Simple build and update workflow
   - `adw_plan_implement_update_task.py` - Complex plan-build-update workflow
   - Tasks can specify workflow with tags: `{opus, adw_plan_implement_update_task}`

3. **Status Updates**
   - Real-time panel-based status messages with timestamps
   - ADW ID and worktree tracking in all outputs
   - Automatic task status updates in `tasks.md`

## Codebase Structure

### Agentic Layer

The agent layer orchestrates AI-powered development workflows:

- `.claude/commands/` - Slash command templates for Claude Code
- `adws/` - AI Developer Workflows (Python orchestration scripts)
- `specs/` - Feature specifications and implementation plans
- `tasks.md` - Central task tracking file

### Application Layer

The target codebase that agents operate on:

- `apps/` - Application code (e.g., sentiment_classification)

## Quick Start

1. **Set up environment**:
   ```bash
   cp .env.sample .env
   # Add your ANTHROPIC_API_KEY
   ```

2. **Add tasks to `tasks.md`**:
   ```markdown
   ## Git Worktree enhance-model
   [] Add cross-validation to sentiment classifier
   [] Implement ensemble model {opus, adw_plan_implement_update_task}
   ```

3. **Run the cron trigger**:
   ```bash
   ./adws/adw_triggers/adw_trigger_cron_todone.py
   ```

The system will automatically:
- Create worktrees as needed
- Process tasks in parallel
- Update task status in real-time
- Handle dependencies and failures

## 12 Leverage Points of Agentic Coding

### In Agent (Core Four)

1. Context
2. Model
3. Prompt
4. Tools

### Through Agent

5. Standard Output
6. Types
7. Docs
8. Tests
9. Architecture
10. Plans
11. Templates
12. AI Developer Workflows

