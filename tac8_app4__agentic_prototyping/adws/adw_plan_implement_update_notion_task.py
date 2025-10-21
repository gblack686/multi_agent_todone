#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pydantic",
#   "python-dotenv",
#   "click",
#   "rich",
# ]
# ///
"""
Run plan, implement, and update task workflow for Notion-based multi-agent task processing.

This script runs three slash commands in sequence:
1. /plan - Creates a plan based on the task description
2. /implement - Implements the plan created by /plan
3. /update_notion_task - Updates the Notion page with the result

This is a Notion-aware version of adw_plan_implement_update_task.py.

Usage:
    # Method 1: Direct execution (requires uv)
    ./adws/adw_plan_implement_update_notion_task.py --adw-id abc123 --worktree-name feature-auth --task "Implement OAuth2" --page-id 247fc382...

    # Method 2: Using uv run
    uv run adws/adw_plan_implement_update_notion_task.py --adw-id abc123 --worktree-name feature-auth --task "Add user profiles" --page-id 247fc382...

Examples:
    # Run with specific model
    ./adws/adw_plan_implement_update_notion_task.py --adw-id abc123 --worktree-name feature-auth --task "Add JWT tokens" --model opus --page-id 247fc382...

    # Run with verbose output
    ./adws/adw_plan_implement_update_notion_task.py --adw-id abc123 --worktree-name feature-auth --task "Fix auth bug" --verbose --page-id 247fc382...
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

# Add the adw_modules directory to the path so we can import agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "adw_modules"))

from agent import (
    AgentTemplateRequest,
    AgentPromptResponse,
    execute_template,
)
from utils import format_agent_status, format_worktree_status


def print_status_panel(
    console,
    action: str,
    adw_id: str,
    worktree: str,
    phase: str = None,
    status: str = "info",
):
    """Print a status panel with timestamp and context.

    Args:
        console: Rich console instance
        action: The action being performed
        adw_id: ADW ID for tracking
        worktree: Worktree/branch name
        phase: Optional phase name (build, plan, etc)
        status: Status type (info, success, error)
    """
    timestamp = datetime.now().strftime("%H:%M:%S")

    # Choose color based on status
    if status == "success":
        border_style = "green"
        icon = "✅"
    elif status == "error":
        border_style = "red"
        icon = "❌"
    else:
        border_style = "cyan"
        icon = "🔄"

    # Build title with context
    title_parts = [f"[{timestamp}]", adw_id[:6], worktree]
    if phase:
        title_parts.append(phase)
    title = " | ".join(title_parts)

    console.print(
        Panel(
            f"{icon} {action}",
            title=f"[bold {border_style}]{title}[/bold {border_style}]",
            border_style=border_style,
            padding=(0, 1),
        )
    )


# Output file name constants
OUTPUT_JSONL = "cc_raw_output.jsonl"
OUTPUT_JSON = "cc_raw_output.json"
FINAL_OBJECT_JSON = "cc_final_object.json"
SUMMARY_JSON = "custom_summary_output.json"


def get_current_commit_hash(working_dir: str) -> Optional[str]:
    """Get the current git commit hash in the working directory."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=working_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()[:9]  # Return first 9 characters of hash
    except subprocess.CalledProcessError:
        return None


@click.command()
@click.option("--adw-id", required=True, help="ADW ID for this task execution")
@click.option(
    "--worktree-name", required=True, help="Name of the git worktree to work in"
)
@click.option("--task", required=True, help="Task description to implement")
@click.option("--page-id", required=True, help="Notion page ID to update with results")
@click.option(
    "--model",
    type=click.Choice(["sonnet", "opus"]),
    default="sonnet",
    help="Claude model to use",
)
@click.option(
    "--prototype",
    type=click.Choice(["uv_script", "vite_vue", "bun_scripts", "uv_mcp"]),
    help="Prototype type for app generation",
)
@click.option("--verbose", is_flag=True, help="Enable verbose output")
def main(
    adw_id: str,
    worktree_name: str,
    task: str,
    page_id: str,
    model: str,
    prototype: Optional[str],
    verbose: bool,
):
    """Run plan, implement, and update task workflow for Notion-based multi-agent processing."""
    console = Console()

    # Sanitize worktree name - extract just the name if it contains extra text
    import re

    # Look for a valid worktree name pattern in the input
    match = re.search(r"([a-z][a-z0-9-]{4,19})", worktree_name)
    if match:
        worktree_name = match.group(1)
    else:
        # Clean up the name
        worktree_name = re.sub(r"[^a-z0-9-]", "-", worktree_name.lower())[:20]
        worktree_name = re.sub(r"-+", "-", worktree_name).strip("-")

    # Calculate the worktree path and the actual working directory
    # With sparse checkout, the worktree contains tac8_app4__agentic_prototyping/
    # and we work within that directory
    worktree_base_path = os.path.abspath(f"trees/{worktree_name}")
    target_directory = "tac8_app4__agentic_prototyping"

    # Check if worktree exists, create if needed
    if not os.path.exists(worktree_base_path):
        console.print(
            Panel(
                f"[bold yellow]Worktree not found at: {worktree_base_path}[/bold yellow]\n\n"
                "Creating worktree now...",
                title="[bold yellow]⚠️  Worktree Missing[/bold yellow]",
                border_style="yellow",
            )
        )

        # Create worktree using the init_worktree command
        init_request = AgentTemplateRequest(
            agent_name="worktree-initializer",
            slash_command="/init_worktree",
            args=[worktree_name, target_directory],
            adw_id=adw_id,
            model=model,
            working_dir=os.getcwd(),  # Run from project root
        )

        # Print start message for worktree creation
        print_status_panel(
            console, "Starting worktree creation", adw_id, worktree_name, "init"
        )

        init_response = execute_template(init_request)

        # Print completion message
        print_status_panel(
            console,
            "Completed worktree creation",
            adw_id,
            worktree_name,
            "init",
            "success",
        )

        if init_response.success:
            console.print(
                Panel(
                    f"[bold green]✅ Worktree created successfully at: {worktree_base_path}[/bold green]",
                    title="[bold green]Worktree Created[/bold green]",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[bold red]Failed to create worktree:\n{init_response.output}[/bold red]",
                    title="[bold red]❌ Worktree Creation Failed[/bold red]",
                    border_style="red",
                )
            )
            sys.exit(1)

    # Set agent names for each phase
    planner_name = f"planner-{worktree_name}"
    builder_name = f"builder-{worktree_name}"
    updater_name = f"notion-updater-{worktree_name}"

    workflow_info = (
        f"[bold blue]Notion Plan-Implement-Update Workflow[/bold blue]\n\n"
        f"[cyan]ADW ID:[/cyan] {adw_id}\n"
        f"[cyan]Worktree:[/cyan] {worktree_name}\n"
        f"[cyan]Task:[/cyan] {task}\n"
        f"[cyan]Page ID:[/cyan] {page_id}\n"
        f"[cyan]Model:[/cyan] {model}\n"
    )

    if prototype:
        workflow_info += f"[cyan]Prototype:[/cyan] {prototype}\n"

    workflow_info += f"[cyan]Working Dir:[/cyan] {worktree_base_path}"

    console.print(
        Panel(
            workflow_info,
            title="[bold blue]🚀 Workflow Configuration[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    # Track workflow state
    workflow_success = True
    plan_path = None
    commit_hash = None
    error_message = None
    plan_response = None
    implement_response = None

    # Phase 1: Run /plan command (or prototype-specific plan command)
    # Determine the plan command based on prototype
    app_name = None  # Initialize for later use
    if prototype:
        plan_command = f"/plan_{prototype}"
        plan_phase_name = f"Prototype Planning ({plan_command})"
        # For prototypes, extract app name from task or use ADW ID
        import re

        app_name_match = re.search(r"app[:\s]+([a-z0-9-]+)", task.lower())
        app_name = app_name_match.group(1) if app_name_match else f"app-{adw_id[:6]}"
        # For prototype plans: adw_id, prompt
        plan_args = [adw_id, task]
    else:
        plan_command = "/plan"
        plan_phase_name = "Planning (/plan)"
        # For regular plan: adw_id, prompt
        plan_args = [adw_id, task]

    console.print(Rule(f"[bold yellow]Phase 1: {plan_phase_name}[/bold yellow]"))
    console.print()

    # Set working directory to include the target_directory path
    agent_working_dir = os.path.join(worktree_base_path, target_directory)

    plan_request = AgentTemplateRequest(
        agent_name=planner_name,
        slash_command=plan_command,
        args=plan_args,
        adw_id=adw_id,
        model=model,
        working_dir=agent_working_dir,
    )

    # Display plan execution info
    plan_info_table = Table(show_header=False, box=None, padding=(0, 1))
    plan_info_table.add_column(style="bold cyan")
    plan_info_table.add_column()

    plan_info_table.add_row("ADW ID", adw_id)
    plan_info_table.add_row("Phase", plan_phase_name)
    plan_info_table.add_row("Command", plan_command)
    plan_info_table.add_row("Args", f'{adw_id} "{task}"')
    if prototype:
        plan_info_table.add_row("Prototype", prototype)
    plan_info_table.add_row("Model", model)
    plan_info_table.add_row("Agent", planner_name)

    console.print(
        Panel(
            plan_info_table,
            title=f"[bold blue]🚀 Plan Inputs | {adw_id} | {worktree_name}[/bold blue]",
            border_style="blue",
        )
    )
    console.print()

    try:
        # Print start message for plan phase
        print_status_panel(
            console, "Starting plan creation", adw_id, worktree_name, "plan"
        )

        # Execute the plan command
        plan_response = execute_template(plan_request)

        # Print completion message
        print_status_panel(
            console,
            f"Completed plan creation: {plan_response.output}",
            adw_id,
            worktree_name,
            "plan",
            "success",
        )

        if plan_response.success:

            plan_path = plan_response.output.strip()

            console.print(
                Panel(
                    (
                        plan_response.output
                        if verbose
                        else f"Plan created successfully at {plan_path}"
                    ),
                    title=f"[bold green]✅ Planning Success | {adw_id} | {worktree_name}[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                )
            )

            # Use the plan output directly as the path
            if plan_path and "specs/" in plan_path and plan_path.endswith(".md"):
                console.print(f"\n[bold cyan]Plan created at:[/bold cyan] {plan_path}")
            else:
                workflow_success = False
                error_message = f"Invalid plan path returned: {plan_path}"
                console.print(
                    Panel(
                        f"[bold red]{error_message}[/bold red]\n\n"
                        "The /plan command should return only the path to the plan file (e.g., 'specs/plan-xyz.md').\n"
                        "Stopping workflow and marking task as failed.",
                        title="[bold red]❌ Critical Error - Invalid Plan Path[/bold red]",
                        border_style="red",
                    )
                )
        else:
            workflow_success = False
            error_message = f"Planning phase failed: {plan_response.output}"
            console.print(
                Panel(
                    plan_response.output,
                    title=f"[bold red]❌ Planning Failed | {adw_id} | {worktree_name}[/bold red]",
                    border_style="red",
                    padding=(1, 2),
                )
            )

        # Save plan phase summary
        plan_output_dir = f"./agents/{adw_id}/{planner_name}"
        plan_summary_path = f"{plan_output_dir}/{SUMMARY_JSON}"

        with open(plan_summary_path, "w") as f:
            json.dump(
                {
                    "phase": "planning",
                    "adw_id": adw_id,
                    "worktree_name": worktree_name,
                    "task": task,
                    "page_id": page_id,
                    "slash_command": plan_command,
                    "args": plan_args,
                    "model": model,
                    "prototype": prototype,
                    "app_name": app_name,
                    "working_dir": agent_working_dir,
                    "success": plan_response.success,
                    "session_id": plan_response.session_id,
                    "plan_path": plan_path,
                },
                f,
                indent=2,
            )

        # Phase 2: Run /implement command (only if planning succeeded)
        if workflow_success and plan_path:
            console.print()
            console.print(
                Rule("[bold yellow]Phase 2: Implementation (/implement)[/bold yellow]")
            )
            console.print()

            implement_request = AgentTemplateRequest(
                agent_name=builder_name,
                slash_command="/implement",
                args=[plan_path],
                adw_id=adw_id,
                model=model,
                working_dir=agent_working_dir,
            )

            # Display implement execution info
            implement_info_table = Table(show_header=False, box=None, padding=(0, 1))
            implement_info_table.add_column(style="bold cyan")
            implement_info_table.add_column()

            implement_info_table.add_row("ADW ID", adw_id)
            implement_info_table.add_row("Phase", "Implementation")
            implement_info_table.add_row("Command", "/implement")
            implement_info_table.add_row("Args", plan_path)
            implement_info_table.add_row("Model", model)
            implement_info_table.add_row("Agent", builder_name)

            console.print(
                Panel(
                    implement_info_table,
                    title=f"[bold blue]🚀 Implement Inputs | {adw_id} | {worktree_name}[/bold blue]",
                    border_style="blue",
                )
            )
            console.print()

            # Print start message for implement phase
            print_status_panel(
                console, "Starting implementation", adw_id, worktree_name, "implement"
            )

            # Execute the implement command
            implement_response = execute_template(implement_request)

            # Print completion message
            print_status_panel(
                console,
                "Completed implementation",
                adw_id,
                worktree_name,
                "implement",
                "success",
            )

            if implement_response.success:
                console.print(
                    Panel(
                        (
                            implement_response.output
                            if verbose
                            else "Implementation completed successfully"
                        ),
                        title=f"[bold green]✅ Implementation Success | {adw_id} | {worktree_name}[/bold green]",
                        border_style="green",
                        padding=(1, 2),
                    )
                )

                # Get the commit hash after successful implementation
                commit_hash = get_current_commit_hash(agent_working_dir)
                if commit_hash:
                    console.print(
                        f"\n[bold cyan]Commit hash:[/bold cyan] {commit_hash}"
                    )
            else:
                workflow_success = False
                error_message = (
                    f"Implementation phase failed: {implement_response.output}"
                )
                console.print(
                    Panel(
                        implement_response.output,
                        title=f"[bold red]❌ Implementation Failed | {adw_id} | {worktree_name}[/bold red]",
                        border_style="red",
                        padding=(1, 2),
                    )
                )

            # Save implement phase summary
            implement_output_dir = f"./agents/{adw_id}/{builder_name}"
            implement_summary_path = f"{implement_output_dir}/{SUMMARY_JSON}"

            with open(implement_summary_path, "w") as f:
                json.dump(
                    {
                        "phase": "implementation",
                        "adw_id": adw_id,
                        "worktree_name": worktree_name,
                        "task": task,
                        "page_id": page_id,
                        "slash_command": "/implement",
                        "args": [plan_path],
                        "model": model,
                        "working_dir": agent_working_dir,
                        "success": implement_response.success,
                        "session_id": implement_response.session_id,
                        "commit_hash": commit_hash,
                    },
                    f,
                    indent=2,
                )
        else:
            # Implementation skipped due to planning issues
            if not workflow_success:
                console.print()
                console.print(
                    Panel(
                        "[yellow]⏭️  Skipping implementation phase due to planning errors[/yellow]",
                        title="[bold yellow]Implementation Skipped[/bold yellow]",
                        border_style="yellow",
                    )
                )

        # Phase 3: Run /update_notion_task command (always run to update status)
        console.print()
        console.print(
            Rule(
                "[bold yellow]Phase 3: Update Notion Task (/update_notion_task)[/bold yellow]"
            )
        )
        console.print()

        # Determine the status to update
        update_status = "Done" if workflow_success and commit_hash else "Failed"

        # Build update content with results
        update_content = {
            "status": update_status,
            "adw_id": adw_id,
            "commit_hash": commit_hash or "",
            "error": error_message or "",
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "workflow": "plan-implement-update",
            "worktree_name": worktree_name,
            "result": (
                implement_response.output
                if implement_response
                else plan_response.output if plan_response else ""
            ),
        }

        update_request = AgentTemplateRequest(
            agent_name=updater_name,
            slash_command="/update_notion_task",
            args=[page_id, update_status, json.dumps(update_content)],
            adw_id=adw_id,
            model=model,
            working_dir=os.getcwd(),  # Run from project root
        )

        # Display update execution info
        update_info_table = Table(show_header=False, box=None, padding=(0, 1))
        update_info_table.add_column(style="bold cyan")
        update_info_table.add_column()

        update_info_table.add_row("ADW ID", adw_id)
        update_info_table.add_row("Phase", "Update Notion Task")
        update_info_table.add_row("Command", "/update_notion_task")
        update_info_table.add_row("Page ID", page_id[:12] + "...")
        update_info_table.add_row("Status", update_status)
        update_info_table.add_row("Model", model)
        update_info_table.add_row("Agent", updater_name)

        console.print(
            Panel(
                update_info_table,
                title=f"[bold blue]🚀 Update Inputs | {adw_id} | {worktree_name}[/bold blue]",
                border_style="blue",
            )
        )
        console.print()

        # Print start message for update phase
        print_status_panel(
            console, "Starting Notion task update", adw_id, worktree_name, "update"
        )

        # Execute the update command
        update_response = execute_template(update_request)

        # Print completion message
        print_status_panel(
            console,
            "Completed Notion task update",
            adw_id,
            worktree_name,
            "update",
            "success",
        )

        if update_response.success:
            console.print(
                Panel(
                    (
                        update_response.output
                        if verbose
                        else "Notion task updated successfully"
                    ),
                    title=f"[bold green]✅ Update Success | {adw_id} | {worktree_name}[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                )
            )
        else:
            console.print(
                Panel(
                    update_response.output,
                    title=f"[bold red]❌ Update Failed | {adw_id} | {worktree_name}[/bold red]",
                    border_style="red",
                    padding=(1, 2),
                )
            )

        # Save update phase summary
        update_output_dir = f"./agents/{adw_id}/{updater_name}"
        update_summary_path = f"{update_output_dir}/{SUMMARY_JSON}"

        with open(update_summary_path, "w") as f:
            json.dump(
                {
                    "phase": "update_notion_task",
                    "adw_id": adw_id,
                    "worktree_name": worktree_name,
                    "task": task,
                    "page_id": page_id,
                    "slash_command": "/update_notion_task",
                    "args": [page_id, update_status, json.dumps(update_content)],
                    "model": model,
                    "working_dir": os.getcwd(),
                    "success": update_response.success,
                    "session_id": update_response.session_id,
                    "final_status": update_status,
                    "result": update_response.output,
                },
                f,
                indent=2,
            )

        # Show workflow summary
        console.print()
        console.print(Rule("[bold blue]Workflow Summary[/bold blue]"))
        console.print()

        summary_table = Table(show_header=True, box=None)
        summary_table.add_column("Phase", style="bold cyan")
        summary_table.add_column("Status", style="bold")
        summary_table.add_column("Output Directory", style="dim")

        # Planning phase row
        planning_status = "✅ Success" if plan_response.success else "❌ Failed"
        summary_table.add_row(
            "Planning (/plan)",
            planning_status,
            f"./agents/{adw_id}/{planner_name}/",
        )

        # Implementation phase row
        if plan_path and workflow_success:
            implement_status = (
                "✅ Success" if implement_response.success else "❌ Failed"
            )
            summary_table.add_row(
                "Implementation (/implement)",
                implement_status,
                f"./agents/{adw_id}/{builder_name}/",
            )
        elif plan_response.success and not plan_path:
            # Plan succeeded but couldn't extract path
            summary_table.add_row(
                "Implementation (/implement)",
                "⏭️ Skipped (no plan path)",
                "-",
            )
        elif not plan_response.success:
            # Plan failed entirely
            summary_table.add_row(
                "Implementation (/implement)",
                "⏭️ Skipped (plan failed)",
                "-",
            )

        # Update phase row
        update_status_display = "✅ Success" if update_response.success else "❌ Failed"
        summary_table.add_row(
            "Update Notion (/update_notion_task)",
            update_status_display,
            f"./agents/{adw_id}/{updater_name}/",
        )

        console.print(summary_table)

        # Create overall workflow summary
        workflow_summary_path = f"./agents/{adw_id}/workflow_summary.json"
        os.makedirs(f"./agents/{adw_id}", exist_ok=True)

        with open(workflow_summary_path, "w") as f:
            json.dump(
                {
                    "workflow": "plan_implement_update_notion_task",
                    "adw_id": adw_id,
                    "worktree_name": worktree_name,
                    "task": task,
                    "page_id": page_id,
                    "model": model,
                    "prototype": prototype,
                    "app_name": app_name,
                    "working_dir": agent_working_dir,
                    "plan_path": plan_path,
                    "commit_hash": commit_hash,
                    "phases": {
                        "planning": {
                            "success": plan_response.success,
                            "session_id": plan_response.session_id,
                            "agent": planner_name,
                        },
                        "implementation": (
                            {
                                "success": (
                                    implement_response.success if plan_path else False
                                ),
                                "session_id": (
                                    implement_response.session_id if plan_path else None
                                ),
                                "agent": builder_name,
                            }
                            if plan_path
                            else None
                        ),
                        "update_notion_task": {
                            "success": update_response.success,
                            "session_id": update_response.session_id,
                            "agent": updater_name,
                        },
                    },
                    "overall_success": workflow_success,
                    "final_task_status": (
                        "Done" if workflow_success and commit_hash else "Failed"
                    ),
                },
                f,
                indent=2,
            )

        console.print(
            f"\n[bold cyan]Workflow summary:[/bold cyan] {workflow_summary_path}"
        )
        console.print()

        # Exit with appropriate code
        if workflow_success:
            console.print(
                "[bold green]✅ Workflow completed successfully![/bold green]"
            )
            sys.exit(0)
        else:
            console.print(
                "[bold yellow]⚠️  Workflow completed with errors[/bold yellow]"
            )
            sys.exit(1)

    except Exception as e:
        console.print(
            Panel(
                f"[bold red]{str(e)}[/bold red]",
                title="[bold red]❌ Unexpected Error[/bold red]",
                border_style="red",
            )
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
