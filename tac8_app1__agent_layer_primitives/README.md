# Agent Layer Primitives

## Value Proposition

This codebase showcases the fundamental building blocks of agentic coding - a new paradigm where we template our engineering and teach agents how to operate our codebases instead of directly modifying them ourselves. Here, we can scale compute to scale our impact.

The Agentic Layer wraps your Application Layer, providing a programmatic interface for AI-driven development workflows.

## Two Approaches to the Agentic Layer

### 1. Minimum Viable Agentic Layer

The simplest implementation to get started with agentic coding:

```
specs/                          # Plans for agents to follow
├── *.md                        # Implementation specifications

.claude/commands/               # Agentic prompts
├── chore.md                    # Planning template
├── implement.md                # Implementation template
└── *.md                        # Other slash commands

adws/                           # AI Developer Workflows
├── adw_modules/
│   └── agent.py                # Core agent execution
└── adw_*.py                    # Top-level workflow scripts (uv single-file)
```

**Key Components:**
- **Plans** (`specs/`): Structured specifications that guide agent actions
- **Prompts** (`.claude/commands/`): Reusable templates for agent interactions
- **Workflows** (`adws/`): Executable scripts that orchestrate agents

### 2. Scaled Agentic Layer

A fully-featured implementation for production-grade agentic development:

```
specs/                          # Plans and specifications
├── issue-*.md                  # Issue-based specs
└── deep_specs/                 # Complex architectural specs

.claude/                        # Agent configuration
├── commands/                   # Agentic prompts
│   ├── bug.md
│   ├── chore.md
│   ├── feature.md
│   ├── test.md
│   ├── e2e/                    # End-to-end test templates
│   │   └── test_*.md
│   └── *.md                    # Domain-specific templates
├── hooks/                      # Event-driven automation
│   ├── pre_tool_use.py
│   ├── post_tool_use.py
│   └── utils/                  # Hook utilities
└── settings.json               # Agent configuration

adws/                           # AI Developer Workflows
├── adw_modules/                # Core logic modules
│   ├── agent.py                # Agent execution
│   ├── data_types.py           # Type definitions
│   ├── git_ops.py              # Git operations
│   ├── github.py               # GitHub integration
│   ├── state.py                # State management
│   └── workflow_ops.py         # Workflow orchestration
├── adw_triggers/               # Workflow triggers
│   ├── trigger_webhook.py      # Webhook-based triggers
│   ├── trigger_cron.py         # Scheduled triggers
│   └── adw_trigger_*.py        # Custom triggers
├── adw_tests/                  # Testing suite
│   ├── test_agents.py
│   └── test_*.py
├── adw_data/                   # Agent database
│   ├── agents.db
│   └── backups/
├── adw_*_iso.py                # Isolated workflows
├── adw_sdlc_*.py               # Full SDLC workflows
└── README.md                   # ADW documentation

agents/                         # Agent output & observability
├── {adw_id}/                   # Per-workflow outputs
│   ├── {agent_name}/           # Per-agent artifacts
│   └── adw_state.json          # Workflow state

ai_docs/                        # AI-generated documentation
├── *.md                        # Generated docs

app_docs/                       # Application documentation
├── feature-*.md                # Feature documentation
└── assets/                     # Supporting materials

trees/                          # Agent worktrees (isolation)
└── {branch_name}/              # Isolated work environments

.mcp.json                       # MCP configuration
```

**Advanced Components:**
- **Types** (`adw_modules/data_types.py`): Strong typing for agent interactions
- **Triggers** (`adw_triggers/`): Multiple invocation patterns (manual, cron, webhooks)
- **Testing** (`adw_tests/`): Validate agent behavior
- **Observability** (`agents/`): Comprehensive logging and debugging
- **Isolation** (`trees/`): Dedicated worktrees for safe agent operations
- **Hooks** (`.claude/hooks/`): Event-driven automation and guardrails

## Flexibility Note

This is just *one way* to organize the agentic layer. The key principle is creating a structured environment where:
- Engineering patterns are templated and reusable
- Agents have clear instructions on how to operate the codebase
- Workflows are composable and scalable
- Output is observable and debuggable

Feel free to adapt this structure to your specific needs and workflows.

## Codebase Structure

### Agentic Layer

The agent layer contains the functionality responsible for agentic coding.
This is where you template your engineering and teach agents how to operate your codebase.

### Application Layer

The application layer contains your actual application code.
This is what your agents will operate on.

`apps/` - Your application code

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

