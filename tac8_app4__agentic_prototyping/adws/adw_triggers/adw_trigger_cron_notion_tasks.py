#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pydantic",
#   "python-dotenv",
#   "click",
#   "rich",
#   "schedule",
# ]
# ///
"""
Notion-based cron trigger for the multi-agent rapid prototyping system.

This script monitors Notion tasks and automatically distributes them to agents.
It runs continuously, checking for eligible tasks at a configurable interval.

Usage:
    # Method 1: Direct execution (requires uv)
    ./adws/adw_triggers/adw_trigger_cron_notion_tasks.py

    # Method 2: Using uv run
    uv run adws/adw_triggers/adw_trigger_cron_notion_tasks.py

    # With custom polling interval (seconds)
    ./adws/adw_triggers/adw_trigger_cron_notion_tasks.py --interval 15

    # Dry run mode (no changes made)
    ./adws/adw_triggers/adw_trigger_cron_notion_tasks.py --dry-run

Examples:
    # Run with custom database ID
    ./adws/adw_triggers/adw_trigger_cron_notion_tasks.py --database-id <notion-db-id>

    # Run once and exit
    ./adws/adw_triggers/adw_trigger_cron_notion_tasks.py --once
"""

import os
import sys
import json
import time
import subprocess
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import click
import schedule
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, "adw_modules"))

from agent import (
    AgentTemplateRequest,
    execute_template,
    generate_short_id,
)

# Import our data models
from data_models import (
    NotionTask,
    NotionCronConfig,
    NotionTaskUpdate,
    WorktreeCreationRequest,
    SystemTag,
)

# Import utility functions
from utils import parse_json

# Configuration constants - get from environment or use fallback
DEFAULT_DATABASE_ID = os.getenv(
    "NOTION_AGENTIC_TASK_TABLE_ID", "247fc382-ac73-8038-9bf6-f0727259e1a3"
)
DEFAULT_APPS_DIRECTORY = "apps"


class NotionTaskManager:
    """Manages Notion task operations using natural language commands."""

    def __init__(self, database_id: str):
        self.database_id = database_id
        self.console = Console()

    def get_eligible_tasks(
        self, status_filter: List[str] = None, limit: int = 10
    ) -> List[NotionTask]:
        """Get eligible tasks from Notion database using /get_notion_tasks command."""
        try:
            if status_filter is None:
                status_filter = ["Not started", "HIL Review"]

            request = AgentTemplateRequest(
                agent_name="notion-task-fetcher",
                slash_command="/get_notion_tasks",
                args=[
                    self.database_id,
                    json.dumps(status_filter),  # Pass as JSON string
                    str(limit),
                ],
                adw_id=generate_short_id(),
                model="sonnet",
                working_dir=os.getcwd(),
            )

            response = execute_template(request)
            if response.success:
                # Parse the JSON response
                try:
                    task_data = parse_json(response.output, list)
                    if task_data:
                        # Convert to NotionTask objects
                        tasks = []
                        for task_dict in task_data:
                            try:
                                # Map the response fields to NotionTask
                                notion_task = NotionTask(
                                    page_id=task_dict.get("page_id"),
                                    title=task_dict.get("title", ""),
                                    status=task_dict.get("status"),
                                    content_blocks=task_dict.get("content_blocks", []),
                                    tags=task_dict.get("tags", {}),
                                    execution_trigger=task_dict.get(
                                        "execution_trigger"
                                    ),
                                    task_prompt=task_dict.get("task_prompt", ""),
                                    worktree=task_dict.get("tags", {}).get("worktree"),
                                    model=task_dict.get("tags", {}).get("model"),
                                    workflow_type=task_dict.get("tags", {}).get(
                                        "workflow"
                                    ),
                                    prototype=task_dict.get("tags", {}).get("prototype"),
                                )
                                if notion_task.is_eligible_for_processing():
                                    tasks.append(notion_task)
                            except Exception as e:
                                self.console.print(
                                    f"[yellow]Warning: Failed to parse task {task_dict.get('page_id', 'unknown')}: {e}[/yellow]"
                                )
                        return tasks
                    else:
                        return []
                except (ValueError, json.JSONDecodeError) as e:
                    error_panel = Panel(
                        f"Failed to parse Notion tasks response: {e}. Text was: {response.output[:500]}",
                        title="[bold red]❌ Parse Error[/bold red]",
                        border_style="red",
                    )
                    self.console.print(error_panel)
                    return []
            else:
                error_panel = Panel(
                    f"Failed to get Notion tasks: {response.output}",
                    title="[bold red]❌ Notion Query Failed[/bold red]",
                    border_style="red",
                )
                self.console.print(error_panel)
                return []

        except Exception as e:
            error_panel = Panel(
                f"Error getting eligible Notion tasks: {str(e)}",
                title="[bold red]❌ Task Retrieval Error[/bold red]",
                border_style="red",
            )
            self.console.print(error_panel)
            return []

    def update_task_status(
        self, page_id: str, status: str, update_content: str = ""
    ) -> bool:
        """Update a Notion task status using /update_notion_task command."""
        try:
            request = AgentTemplateRequest(
                agent_name="notion-task-updater",
                slash_command="/update_notion_task",
                args=[page_id, status, update_content],
                adw_id=generate_short_id(),
                model="sonnet",
                working_dir=os.getcwd(),
            )

            response = execute_template(request)
            if response.success:
                return True
            else:
                error_panel = Panel(
                    f"Failed to update Notion task status: {response.output}",
                    title="[bold red]❌ Status Update Failed[/bold red]",
                    border_style="red",
                )
                self.console.print(error_panel)
                return False
        except Exception as e:
            error_panel = Panel(
                f"Error updating Notion task status: {str(e)}",
                title="[bold red]❌ Status Update Error[/bold red]",
                border_style="red",
            )
            self.console.print(error_panel)
            return False

    def generate_worktree_name(
        self, task_description: str, prefix: str = ""
    ) -> Optional[str]:
        """Generate a worktree name using /make_worktree_name command."""
        try:
            request = AgentTemplateRequest(
                agent_name="worktree-namer",
                slash_command="/make_worktree_name",
                args=[task_description, prefix],
                adw_id=generate_short_id(),
                model="sonnet",
                working_dir=os.getcwd(),
            )

            response = execute_template(request)
            if response.success:
                # Trust the prompt to return just the worktree name
                worktree_name = response.output.strip()
                
                # Display the generated worktree name in a panel
                name_panel = Panel(
                    f"[bold cyan]{worktree_name}[/bold cyan]",
                    title="[bold blue]📁 Generated Worktree Name[/bold blue]",
                    border_style="blue",
                    padding=(0, 2),
                )
                self.console.print(name_panel)
                
                return worktree_name
            else:
                self.console.print(
                    f"[red]Error: Failed to generate worktree name[/red]"
                )
                return None
        except Exception as e:
            self.console.print(f"[red]Error generating worktree name: {e}[/red]")
            return None


class NotionCronTrigger:
    """Main Notion-based cron trigger implementation."""

    def __init__(self, config: NotionCronConfig):
        self.config = config
        self.console = Console()
        self.task_manager = NotionTaskManager(config.database_id)
        self.running = True
        self.stats = {
            "checks": 0,
            "tasks_started": 0,
            "worktrees_created": 0,
            "notion_updates": 0,
            "errors": 0,
            "last_check": None,
        }

    def check_worktree_exists(self, worktree_name: str) -> bool:
        """Check if a worktree already exists."""
        worktree_path = Path(self.config.worktree_base_path) / worktree_name
        return worktree_path.exists()

    def create_worktree(self, worktree_name: str) -> bool:
        """Create a new worktree using the init_worktree command."""
        if self.config.dry_run:
            self.console.print(
                f"[yellow]DRY RUN: Would create worktree '{worktree_name}'[/yellow]"
            )
            return True

        try:
            # For this project, always use the current project directory for sparse checkout
            target_directory = "tac8_app4__agentic_prototyping"

            request = AgentTemplateRequest(
                agent_name="worktree-creator",
                slash_command="/init_worktree",
                args=[worktree_name, target_directory],
                adw_id=generate_short_id(),
                model="sonnet",
                working_dir=os.getcwd(),
            )

            response = execute_template(request)
            if response.success:
                self.stats["worktrees_created"] += 1
                success_panel = Panel(
                    f"✓ Created worktree: {worktree_name} → {target_directory}",
                    title="[bold green]Worktree Created[/bold green]",
                    border_style="green",
                )
                self.console.print(success_panel)
                return True
            else:
                error_panel = Panel(
                    f"Failed to create worktree: {worktree_name}",
                    title="[bold red]❌ Worktree Creation Failed[/bold red]",
                    border_style="red",
                )
                self.console.print(error_panel)
                self.stats["errors"] += 1
                return False
        except Exception as e:
            error_panel = Panel(
                f"Error creating worktree: {str(e)}",
                title="[bold red]❌ Worktree Creation Error[/bold red]",
                border_style="red",
            )
            self.console.print(error_panel)
            self.stats["errors"] += 1
            return False

    def delegate_task(self, task: NotionTask, worktree_name: str, adw_id: str):
        """Delegate a Notion task to the appropriate workflow."""

        # Determine workflow and model
        # If prototype is specified, always use full workflow for proper routing
        use_full_workflow = task.should_use_full_workflow() or task.prototype is not None
        model = task.get_preferred_model()

        if self.config.dry_run:
            workflow_type = (
                "plan-implement-update" if use_full_workflow else "build-update"
            )
            self.console.print(
                f"[yellow]DRY RUN: Would delegate task '{task.title}' (page: {task.page_id[:8]}...) with ADW ID {adw_id} using {workflow_type} workflow with {model} model[/yellow]"
            )
            return

        try:
            # Determine which workflow script to use
            if use_full_workflow:
                workflow_script = "adw_plan_implement_update_notion_task.py"
                workflow_type = "plan-implement-update"
                slash_command_for_display = "/plan + /implement + /update_notion_task"
            else:
                workflow_script = "adw_build_update_notion_task.py"
                workflow_type = "build-update"
                slash_command_for_display = "/build + /update_notion_task"

            # Build the command to run the workflow
            # Combine title and prompt for better context
            combined_task = (
                f"{task.title}: {task.task_prompt}" if task.task_prompt else task.title
            )
            cmd = [
                "uv",
                "run",
                os.path.join(parent_dir, workflow_script),
                "--adw-id",
                adw_id,
                "--worktree-name",
                worktree_name,
                "--task",
                combined_task,
                "--page-id",
                task.page_id,
                "--model",
                model,
            ]
            
            # Add prototype flag if specified
            if task.prototype:
                cmd.extend(["--prototype", task.prototype])

            # Create a panel showing the agent execution details
            exec_details = f"[bold]Page ID:[/bold] {task.page_id}\n"
            exec_details += f"[bold]Title:[/bold] {task.title}\n"
            exec_details += f"[bold]Slash Command:[/bold] {slash_command_for_display}\n"
            exec_details += f"[bold]Arguments:[/bold]\n"
            exec_details += f"  • ADW ID: {adw_id}\n"
            exec_details += f"  • Worktree: {worktree_name}\n"
            exec_details += f"  • Task: {task.task_prompt[:50]}{'...' if len(task.task_prompt or '') > 50 else ''}\n"
            exec_details += f"  • Model: {model}\n"
            exec_details += f"  • Workflow: {workflow_type}\n"

            if task.tags:
                tags_str = ", ".join([f"{k}: {v}" for k, v in task.tags.items()])
                exec_details += f"  • Tags: {tags_str}"

            exec_panel = Panel(
                exec_details,
                title="[bold cyan]🤖 Executing Notion Agent[/bold cyan]",
                border_style="cyan",
                padding=(1, 2),
            )
            self.console.print(exec_panel)

            # Run the workflow in a subprocess
            # Use start_new_session=True to detach the process and let it survive parent death
            result = subprocess.Popen(cmd, start_new_session=True)
            self.stats["tasks_started"] += 1

            # Create success panel for task delegation
            delegation_panel = Panel(
                f"✓ Task delegated with ADW ID: {adw_id}",
                title="[bold green]✅ Notion Task Delegated[/bold green]",
                border_style="green",
            )
            self.console.print(delegation_panel)

        except Exception as e:
            error_panel = Panel(
                f"Error delegating Notion task: {str(e)}",
                title="[bold red]❌ Delegation Failed[/bold red]",
                border_style="red",
            )
            self.console.print(error_panel)
            self.stats["errors"] += 1

    def process_tasks(self):
        """Main task processing logic for Notion tasks."""
        self.stats["checks"] += 1
        self.stats["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Get eligible tasks from Notion
        eligible_tasks = self.task_manager.get_eligible_tasks(
            status_filter=self.config.status_filter,
            limit=self.config.max_concurrent_tasks,
        )

        if not eligible_tasks:
            info_panel = Panel(
                f"No eligible tasks found in Notion database. Add tasks with 'execute' or 'continue -' triggers.",
                title="[bold yellow]No Notion Tasks[/bold yellow]",
                border_style="yellow",
            )
            self.console.print(info_panel)
            return

        # Report tasks that will be processed
        task_summary_lines = []
        for task in eligible_tasks:
            tags_str = ""
            if task.tags:
                tags_list = [f"{k}: {v}" for k, v in task.tags.items()]
                tags_str = f" [dim]({', '.join(tags_list)})[/dim]"

            task_summary_lines.append(f"  • {task.title}{tags_str}")
            task_summary_lines.append(
                f"    [dim]Status: {task.status} | Trigger: {task.execution_trigger} | Page: {task.page_id[:12]}...[/dim]"
            )

        if task_summary_lines:
            tasks_panel = Panel(
                "\n".join(task_summary_lines),
                title=f"[bold green]🚀 Processing {len(eligible_tasks)} Notion Task{'s' if len(eligible_tasks) != 1 else ''}[/bold green]",
                border_style="green",
            )
            self.console.print(tasks_panel)

        # Process each task
        for task in eligible_tasks:
            try:
                # Generate ADW ID for this task
                adw_id = generate_short_id()

                # IMMEDIATELY update task status to "In progress" in Notion
                # This marks the task as being picked up BEFORE any processing
                if not self.config.dry_run:
                    update_content = {
                        "status": "In progress",
                        "adw_id": adw_id,
                        "timestamp": datetime.now().isoformat(),
                        "trigger": task.execution_trigger,
                        "previous_status": task.status,
                    }
                    success = self.task_manager.update_task_status(
                        task.page_id, "In progress", json.dumps(update_content)
                    )
                    if not success:
                        error_panel = Panel(
                            f"Failed to update Notion task status: {task.title}",
                            title="[bold red]❌ Notion Update Failed[/bold red]",
                            border_style="red",
                        )
                        self.console.print(error_panel)
                        self.stats["errors"] += 1
                        continue

                    self.stats["notion_updates"] += 1

                    # Success panel for status update
                    update_panel = Panel(
                        f"✓ Updated Notion task to 'In progress': {task.title}",
                        title="[bold green]✅ Task Claimed[/bold green]",
                        border_style="green",
                    )
                    self.console.print(update_panel)
                else:
                    self.console.print(
                        f"[yellow]DRY RUN: Would update Notion task '{task.title}' to 'In progress' with ADW ID {adw_id}[/yellow]"
                    )

                # Generate or extract worktree name
                if task.worktree:
                    worktree_name = task.worktree
                else:
                    # Generate worktree name
                    worktree_name = self.task_manager.generate_worktree_name(
                        task.task_prompt or task.title, "task"
                    )
                    if not worktree_name:
                        self.console.print(
                            f"[red]Failed to generate worktree name for task: {task.title}[/red]"
                        )
                        # If we updated status but can't proceed, mark as failed
                        if not self.config.dry_run:
                            self.task_manager.update_task_status(
                                task.page_id,
                                "Failed",
                                "Failed to generate worktree name",
                            )
                        continue

                # Check if worktree exists, create if needed
                if not self.check_worktree_exists(worktree_name):
                    info_panel = Panel(
                        f"Worktree '{worktree_name}' doesn't exist, creating...",
                        title="[bold yellow]ℹ️ Creating Worktree[/bold yellow]",
                        border_style="yellow",
                    )
                    self.console.print(info_panel)
                    if not self.create_worktree(worktree_name):
                        # If we updated status but can't proceed, mark as failed
                        if not self.config.dry_run:
                            self.task_manager.update_task_status(
                                task.page_id, "Failed", "Failed to create worktree"
                            )
                        continue  # Skip this task if worktree creation failed

                # Delegate task to appropriate workflow
                self.delegate_task(task, worktree_name, adw_id)

                # Respect max concurrent tasks limit
                if self.stats["tasks_started"] >= self.config.max_concurrent_tasks:
                    warning_panel = Panel(
                        f"Reached max concurrent tasks ({self.config.max_concurrent_tasks})",
                        title="[bold yellow]⚠️ Task Limit[/bold yellow]",
                        border_style="yellow",
                    )
                    self.console.print(warning_panel)
                    break

            except Exception as e:
                error_panel = Panel(
                    f"Error processing Notion task: {str(e)}",
                    title="[bold red]❌ Task Processing Error[/bold red]",
                    border_style="red",
                )
                self.console.print(error_panel)
                self.stats["errors"] += 1
                continue

    def create_status_display(self) -> Panel:
        """Create a status display panel for Notion operations."""
        table = Table(show_header=False, box=None)
        table.add_column(style="bold cyan")
        table.add_column()

        table.add_row(
            "Status", "[green]Running[/green]" if self.running else "[red]Stopped[/red]"
        )
        table.add_row("Polling Interval", f"{self.config.polling_interval} seconds")
        table.add_row("Notion Database", f"{self.config.database_id[:12]}...")
        table.add_row("Status Filter", str(self.config.status_filter))
        table.add_row("Max Concurrent", str(self.config.max_concurrent_tasks))
        table.add_row("Dry Run", "Yes" if self.config.dry_run else "No")
        table.add_row("", "")
        table.add_row("Checks", str(self.stats["checks"]))
        table.add_row("Tasks Started", str(self.stats["tasks_started"]))
        table.add_row("Worktrees Created", str(self.stats["worktrees_created"]))
        table.add_row("Notion Updates", str(self.stats["notion_updates"]))
        table.add_row("Errors", str(self.stats["errors"]))
        table.add_row("Last Check", self.stats["last_check"] or "Never")

        return Panel(
            Align.center(table),
            title="[bold blue]🔄 Notion Multi-Agent Cron[/bold blue]",
            border_style="blue",
        )

    def run_once(self):
        """Run the task check once and exit."""
        self.console.print(self.create_status_display())
        self.console.print("\n[yellow]Running single Notion check...[/yellow]\n")
        self.process_tasks()
        self.console.print("\n[green]✅ Single Notion check completed[/green]")

    def run_continuous(self):
        """Run continuously with scheduled checks."""
        # Schedule the task processing
        schedule.every(self.config.polling_interval).seconds.do(self.process_tasks)

        self.console.print(self.create_status_display())
        self.console.print(
            f"\n[green]Started monitoring Notion tasks every {self.config.polling_interval} seconds[/green]"
        )
        self.console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            self.console.print("\n[yellow]Stopping Notion cron trigger...[/yellow]")
            self.console.print(self.create_status_display())
            self.console.print("[green]✅ Notion cron trigger stopped[/green]")


@click.command()
@click.option(
    "--interval", type=int, default=15, help="Polling interval in seconds (default: 15)"
)
@click.option(
    "--database-id",
    type=str,
    default=DEFAULT_DATABASE_ID,
    help=f"Notion database ID (default: from NOTION_AGENTIC_TASK_TABLE_ID env var)",
)
@click.option(
    "--dry-run", is_flag=True, help="Run in dry-run mode without making changes"
)
@click.option(
    "--max-tasks", type=int, default=3, help="Maximum concurrent tasks (default: 3)"
)
@click.option(
    "--once", is_flag=True, help="Run once and exit instead of continuous monitoring"
)
@click.option(
    "--status-filter",
    type=str,
    default='["Not started", "HIL Review"]',
    help='Status filter as JSON array (default: ["Not started", "HIL Review"])',
)
def main(
    interval: int,
    database_id: str,
    dry_run: bool,
    max_tasks: int,
    once: bool,
    status_filter: str,
):
    """Monitor and distribute tasks from the Notion Agentic Prototyper database."""
    console = Console()

    # Check if database ID is properly configured
    if not database_id:
        console.print(
            Panel(
                "[bold red]No Notion database ID configured![/bold red]\n\n"
                "Please set the NOTION_AGENTIC_TASK_TABLE_ID environment variable in your .env file\n"
                "or provide it via --database-id option.",
                title="[bold red]❌ Configuration Error[/bold red]",
                border_style="red",
            )
        )
        sys.exit(1)

    try:
        # Parse status filter
        parsed_status_filter = json.loads(status_filter)
        if not isinstance(parsed_status_filter, list):
            raise ValueError("Status filter must be a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[red]Error parsing status filter: {e}[/red]")
        console.print(f"[yellow]Using default: ['Not started', 'HIL Review'][/yellow]")
        parsed_status_filter = ["Not started", "HIL Review"]

    # Create configuration
    config = NotionCronConfig(
        database_id=database_id,
        polling_interval=interval,
        dry_run=dry_run,
        max_concurrent_tasks=max_tasks,
        status_filter=parsed_status_filter,
    )

    # Create and run the trigger
    trigger = NotionCronTrigger(config)

    if once:
        trigger.run_once()
    else:
        trigger.run_continuous()


if __name__ == "__main__":
    main()
