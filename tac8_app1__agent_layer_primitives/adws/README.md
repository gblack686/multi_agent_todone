# AI Developer Workflows (ADWs)

## Overview

The `adws/` directory contains the **AI Developer Workflows** - the highest compositional level of the agentic layer. These are executable Python scripts that combine deterministic code with non-deterministic, compute-scalable agents to perform complex development tasks on your application layer.

ADWs represent a paradigm shift: instead of directly modifying code ourselves, we template our engineering patterns and teach agents how to operate our codebases. This allows us to scale compute to scale our impact.

## Core Philosophy

- **Template Engineering**: Capture and reuse engineering patterns
- **Agent Orchestration**: Combine multiple agents for complex workflows
- **Compute Scalability**: Scale development effort through parallel agent execution
- **Observability**: Track and debug agent actions through structured outputs

## Architecture Evolution

### Minimum Viable ADW Structure

```
adws/
   adw_modules/
       agent.py                # Core agent execution module
   adw_*.py                    # Single-file workflow scripts (uv astral)
```

The minimum viable structure focuses on:
- **Core execution** (`agent.py`): Essential agent interaction logic
- **Simple workflows** (`adw_*.py`): Standalone scripts using uv for dependency management

### Scaled ADW Structure

```
adws/
   adw_modules/                # Core reusable modules
       agent.py                # Agent execution
       agent_sdk.py            # SDK-based execution
       data_types.py           # Type definitions
       git_ops.py              # Git operations
       github.py               # GitHub integration
       state.py                # State management
       workflow_ops.py         # Workflow orchestration
       worktree_ops.py         # Worktree management
   
   adw_triggers/               # Invocation patterns
       trigger_webhook.py      # Webhook-based triggers
       trigger_cron.py         # Scheduled execution
       adw_trigger_*.py        # Custom triggers
   
   adw_tests/                  # Testing infrastructure
       test_agents.py          # Agent behavior tests
       test_*.py               # Component tests
   
   adw_data/                   # Persistent storage
       agents.db               # Agent database
       backups/                # Database backups
   
   # Individual workflows
   adw_plan_iso.py             # Planning workflow
   adw_build_iso.py            # Build workflow
   adw_test_iso.py             # Testing workflow
   adw_review_iso.py           # Review workflow
   adw_document_iso.py         # Documentation workflow
   adw_patch_iso.py            # Patching workflow
   
   # Composed workflows
   adw_plan_build_iso.py       # Plan + Build
   adw_plan_build_test_iso.py  # Plan + Build + Test
   adw_sdlc_iso.py             # Full SDLC workflow
   adw_sdlc_zte_iso.py         # Zero-touch engineering
   adw_ship_iso.py             # Ship to production
```

## Key Components

### 1. Core Module: `agent.py`

The foundation module that provides:
- **AgentPromptRequest/Response**: Data models for prompt execution
- **AgentTemplateRequest**: Data model for slash command execution
- **prompt_claude_code()**: Direct Claude Code CLI execution
- **prompt_claude_code_with_retry()**: Execution with automatic retry logic
- **execute_template()**: Slash command template execution
- **Environment management**: Safe subprocess environment handling
- **Output parsing**: JSONL to JSON conversion and result extraction

### 2. Direct Prompt Execution: `adw_prompt.py`

Execute adhoc Claude Code prompts from the command line.

**Usage:**
```bash
# Direct execution (requires uv)
./adws/adw_prompt.py "Write a hello world Python script"

# With specific model
./adws/adw_prompt.py "Explain this code" --model opus

# From different directory
./adws/adw_prompt.py "List files here" --working-dir /path/to/project
```

**Features:**
- Direct prompt execution without templates
- Configurable models (sonnet/opus)
- Custom output paths
- Automatic retry on failure
- Rich console output with progress indicators

### 3. Slash Command Execution: `adw_slash_command.py`

Execute predefined slash commands from `.claude/commands/*.md` templates.

**Usage:**
```bash
# Run a slash command
./adws/adw_slash_command.py /chore "Add logging to agent.py"

# With arguments
./adws/adw_slash_command.py /implement specs/feature.md

# Start a new session
./adws/adw_slash_command.py /start
```

**Available Commands:**
- `/chore` - Create implementation plans
- `/implement` - Execute implementation plans
- `/prime` - Prime the agent with context
- `/start` - Start a new agent session

### 4. Compound Workflow: `adw_chore_implement.py`

Orchestrates a two-phase workflow: planning (/chore) followed by implementation (/implement).

**Usage:**
```bash
# Plan and implement a feature
./adws/adw_chore_implement.py "Add error handling to all API endpoints"

# With specific model
./adws/adw_chore_implement.py "Refactor database logic" --model opus
```

**Workflow Phases:**
1. **Planning Phase**: Executes `/chore` to create a detailed plan
2. **Implementation Phase**: Automatically executes `/implement` with the generated plan

## SDK-Based ADWs

In addition to subprocess-based execution, ADWs now support the Claude Code Python SDK for better type safety and native async/await patterns.

### SDK Module: `agent_sdk.py`

The SDK module provides idiomatic patterns for using the Claude Code Python SDK:
- **Simple queries** - `simple_query()` for basic text responses  
- **Tool-enabled queries** - `query_with_tools()` for operations requiring tools
- **Interactive sessions** - `create_session()` context manager for conversations
- **Error handling** - `safe_query()` with SDK-specific exception handling

### SDK Execution: `adw_sdk_prompt.py`

Execute Claude Code using the Python SDK instead of subprocess.

**Usage:**
```bash
# One-shot query
./adws/adw_sdk_prompt.py "Write a hello world Python script"

# Interactive session  
./adws/adw_sdk_prompt.py --interactive

# With tools
./adws/adw_sdk_prompt.py "Create hello.py" --tools Write,Read

# Interactive with context
./adws/adw_sdk_prompt.py --interactive --context "Debugging a memory leak"
```

### SDK vs Subprocess

| Feature | Subprocess (agent.py) | SDK (agent_sdk.py) |
|---------|----------------------|-------------------|
| Type Safety | Basic dictionaries | Typed message objects |
| Error Handling | Generic exceptions | SDK-specific exceptions |
| Async Support | Subprocess management | Native async/await |
| Interactive Sessions | Not supported | ClaudeSDKClient |

## Output Structure & Observability

### Minimum Viable Output

```
agents/
   {adw_id}/                   # Unique 8-character ID per execution
       {agent_name}/            # Agent-specific outputs
          cc_raw_output.jsonl  # Raw streaming output
          cc_final_object.json # Final result object
```

### Scaled Output Structure

```
agents/                         # Comprehensive observability
   {adw_id}/                   # Unique workflow execution
       adw_state.json          # Workflow state tracking
       
       # Per-agent outputs
       {agent_name}/
          cc_raw_output.jsonl  # Raw streaming output
          cc_raw_output.json   # Parsed JSON array
          cc_final_object.json # Final result object
          custom_summary_output.json # High-level summary
       
       # Specialized agent outputs
       branch_generator/       # Branch naming
       issue_classifier/       # Issue categorization
       sdlc_planner/          # SDLC planning
       sdlc_implementor/      # Implementation
       reviewer/              # Code review
       documenter/            # Documentation
       
       # Workflow metadata
       workflow_summary.json   # Overall summary
       workflow_metrics.json   # Performance metrics
```

This structure provides:
- **Debugging**: Raw outputs for troubleshooting
- **Analysis**: Structured JSON for programmatic processing
- **Metrics**: Performance and success tracking
- **Audit Trail**: Complete history of agent actions

## Data Flow

1. **Input**: User provides prompt/command + arguments
2. **Template Composition**: ADW loads slash command template from `.claude/commands/`
3. **Execution**: Claude Code CLI processes the prompt
4. **Output Parsing**: JSONL stream parsed into structured JSON
5. **Result Storage**: Multiple output formats saved for analysis

## Key Features

### Retry Logic
- Automatic retry for transient failures
- Configurable retry attempts and delays
- Different retry codes for various error types

### Environment Safety
- Filtered environment variables for subprocess execution
- Only passes required variables (API keys, paths, etc.)
- Prevents environment variable leakage

### Rich Console UI
- Progress indicators during execution
- Colored output panels for success/failure
- Structured tables showing inputs and outputs
- File path listings for generated outputs

### Session Tracking
- Unique ADW IDs for each execution
- Session IDs from Claude Code for debugging
- Comprehensive logging and output capture

## Best Practices

1. **Use the Right Tool**:
   - `adw_prompt.py` for one-off tasks
   - `adw_slash_command.py` for templated operations
   - `adw_chore_implement.py` for complex features
   - `adw_sdk_prompt.py` for type-safe SDK operations or interactive sessions

2. **Model Selection**:
   - Use `sonnet` (default) for most tasks
   - Use `opus` for complex reasoning or large codebases

3. **Working Directory**:
   - Always specify `--working-dir` when operating on different projects
   - ADWs respect `.mcp.json` configuration in working directories

4. **Output Analysis**:
   - Check `custom_summary_output.json` for high-level results
   - Use `cc_final_object.json` for the final agent response
   - Review `cc_raw_output.jsonl` for debugging

## Integration Points

### Core Integrations

- **Slash Commands** (`.claude/commands/*.md`): Templated agent prompts
- **Application Layer** (`apps/*`): Target codebase for modifications
- **Specifications** (`specs/*`): Implementation plans and requirements
- **AI Documentation** (`ai_docs/*`): Context and reference materials

### Extended Integrations (Scaled)

- **Worktrees** (`trees/*`): Isolated environments for agent operations
- **MCP Configuration** (`.mcp.json`): Model Context Protocol settings
- **Hooks** (`.claude/hooks/*`): Event-driven automation
- **Deep Specs** (`deep_specs/*`): Complex architectural specifications
- **App Documentation** (`app_docs/*`): Generated feature documentation
- **GitHub Integration**: Issue tracking, PR creation, and automation
- **External Services**: Webhooks, CI/CD, monitoring systems

## Error Handling

ADWs implement robust error handling:
- Installation checks for Claude Code CLI
- Timeout protection (5-minute default)
- Graceful failure with informative error messages
- Retry codes for different failure types
- Output truncation to prevent console flooding

## Flexibility & Customization

The ADW structure is intentionally flexible. This is just *one way* to organize your agentic layer. Key principles to maintain:

1. **Separation of Concerns**: Keep agent logic separate from application code
2. **Composability**: Build complex workflows from simple components
3. **Observability**: Maintain clear audit trails of agent actions
4. **Scalability**: Design for parallel execution and compute scaling
5. **Testability**: Ensure agent behavior can be validated

Adapt the structure to your team's needs, development patterns, and scale requirements.

## Getting Started

### Minimum Viable Setup

1. Create basic ADW structure:
   ```bash
   mkdir -p adws/adw_modules
   mkdir -p specs
   mkdir -p .claude/commands
   ```

2. Add core agent module (`adw_modules/agent.py`)
3. Create your first workflow script (`adw_prompt.py`)
4. Define slash commands (`.claude/commands/chore.md`)

### Scaling Up

As your needs grow, incrementally add:
- Type definitions for better IDE support
- Triggers for automation
- Tests for reliability
- State management for complex workflows
- Worktrees for isolation
- Metrics for performance tracking

---

The ADW layer represents the pinnacle of abstraction in agentic coding, turning high-level developer intentions into executed code changes through intelligent agent orchestration. It's where we scale our impact by scaling compute, not just effort.