#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "aiosqlite"]
# ///

"""
ADW AEA Patch - Agent Embedded Application patch workflow

Key differences from adw_patch_iso.py:
1. No worktree creation - works on current branch
2. Database-driven state management
3. Updates agent conversation in database
4. Simplified workflow for interactive use
5. Extracts simplified response from raw_output.json
6. Uses CLAUDE_CODE_PATH environment variable for Claude CLI

SESSION RESUMPTION FLOW:
1. Server receives prompt with agent_id
2. Server fetches agent from DB (includes cc_session_id if exists)
3. Server launches this script with agent_id
4. This script fetches agent from DB again (to get latest state)
5. If cc_session_id exists: uses --resume flag to continue conversation
6. If no cc_session_id: creates new session, captures and stores session ID
7. This ensures conversation context is maintained across:
   - Multiple prompts in same session
   - Application refreshes/restarts
   - Server restarts (as long as DB persists)
"""

import sys
import json
import asyncio
import subprocess
import tempfile
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dotenv import load_dotenv
from adw_modules.utils import get_safe_subprocess_env

import aiosqlite

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))
from adw_modules.aea_data_types import AEAAgent, AEAMessage

# Load environment variables
load_dotenv()

# Get Claude Code CLI path from environment (mirroring adw_modules/agent.py)
CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")

# Database path
DB_PATH = Path(__file__).parent / "adw_data" / "aea_agents.db"


def check_claude_installed() -> Optional[str]:
    """Check if Claude Code CLI is installed. Return error message if not."""
    try:
        result = subprocess.run(
            [CLAUDE_PATH, "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return f"Error: Claude Code CLI is not installed or not working. Expected at: {CLAUDE_PATH}"
    except FileNotFoundError:
        return f"Error: Claude Code CLI is not installed. Expected at: {CLAUDE_PATH}"
    return None


def parse_jsonl_output(output_file: Path) -> Tuple[str, str, Optional[str]]:
    """
    Parse JSONL output file and extract the result message and session ID.
    Mirrors the logic from adw_modules/agent.py

    Returns:
        tuple: (simplified_message, full_json_string, session_id)
    """
    try:
        with open(output_file, "r") as f:
            # Read all lines and parse each as JSON
            messages = []
            for line in f:
                if line.strip():
                    try:
                        messages.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            # Store complete output as JSON array
            full_output = json.dumps(messages, indent=2)

            # Extract session_id from the first message (type="system", subtype="init")
            session_id = None
            for message in messages:
                if message.get("type") == "system" and message.get("subtype") == "init":
                    session_id = message.get("session_id")
                    break
                # Also check other message types that might have session_id
                elif "session_id" in message:
                    session_id = message.get("session_id")
                    break

            # Find the result message (should be the last one with type="result")
            result_message = None
            for message in reversed(messages):
                if message.get("type") == "result":
                    # Check for error conditions
                    subtype = message.get("subtype", "")
                    if subtype == "error_during_execution":
                        result_message = (
                            "Error during execution: Agent encountered an error"
                        )
                    else:
                        result_message = message.get("result", "No result found")
                    break

            # Fallback if no result type found - try to find assistant message
            if result_message is None:
                for message in reversed(messages):
                    if message.get("type") == "assistant":
                        content = message.get("message", {}).get("content", [])
                        if content and isinstance(content, list):
                            text_content = next(
                                (
                                    c.get("text")
                                    for c in content
                                    if c.get("type") == "text"
                                ),
                                None,
                            )
                            if text_content:
                                result_message = text_content
                                break

            if result_message is None:
                result_message = "Agent completed but no response found"

            return result_message, full_output, session_id

    except (FileNotFoundError, json.JSONDecodeError) as e:
        return f"Error reading output: {str(e)}", "[]", None


async def get_agent_from_db(agent_id: str) -> Optional[AEAAgent]:
    """Fetch agent from database - ALWAYS retrieves existing agent with session ID"""
    print(f"[adw_aea_patch] Fetching agent {agent_id} from database...")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM aea_agents WHERE agent_id = ?", (agent_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                agent = AEAAgent(
                    id=row["id"],
                    agent_id=row["agent_id"],
                    agent_name=row["agent_name"],
                    adw_id=row["adw_id"],
                    cc_session_id=row["cc_session_id"],
                    conversation=json.loads(row["conversation"]),
                    full_output=row["full_output"],
                    state=row["state"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    archived=bool(row["archived"]),
                )
                print(f"[adw_aea_patch] Found agent {agent_id}:")
                print(f"  - Claude session ID: {agent.cc_session_id or 'None'}")
                print(f"  - Messages in conversation: {len(agent.conversation)}")
                return agent
    print(f"[adw_aea_patch] ERROR: Agent {agent_id} not found in database!")
    return None


async def update_agent_in_db(agent: AEAAgent):
    """Update agent in database"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE aea_agents 
            SET conversation = ?, full_output = ?, state = ?, 
                updated_at = ?, cc_session_id = ?
            WHERE agent_id = ?
            """,
            (
                json.dumps([msg.model_dump() for msg in agent.conversation]),
                agent.full_output,
                agent.state,
                datetime.now().isoformat(),
                agent.cc_session_id,
                agent.agent_id,
            ),
        )
        await db.commit()


async def execute_claude_code(
    prompt: str, agent_id: str, cc_session_id: Optional[str] = None
) -> Tuple[str, str, Optional[str]]:
    """
    Execute Claude Code CLI with the given prompt.
    Mirrors the approach in adw_modules/agent.py

    Args:
        prompt: The prompt to send to Claude
        agent_id: Our internal agent ID
        cc_session_id: Claude Code session ID (if known from previous prompt)

    Returns:
        tuple: (result_message, full_output_json, session_id)
    """
    # Check if Claude is installed
    error_msg = check_claude_installed()
    if error_msg:
        return error_msg, "[]", None

    # Create temporary directory for this session
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        output_path = temp_path / "raw_output.jsonl"

        # Build Claude command (mirroring adw_modules/agent.py pattern)
        cmd = [CLAUDE_PATH, "-p", prompt]
        cmd.extend(["--output-format", "stream-json"])
        cmd.append("--verbose")

        # Use existing session ID if available, otherwise let Claude create one
        if cc_session_id:
            # Use --resume flag for existing sessions to maintain conversation context
            cmd.extend(["--resume", cc_session_id])
            print(f"✓ Resuming Claude session {cc_session_id} for agent {agent_id}")
            print(f"  This ensures conversation context is maintained across prompts")
        else:
            print(f"Creating new Claude session for agent {agent_id}")
            print(f"  Session ID will be captured and stored for future prompts")

        # Add dangerous skip permissions flag for AEA (since it's interactive)
        cmd.append("--dangerously-skip-permissions")

        print(f"Executing Claude Code for agent {agent_id}...")
        print(f"Using Claude at: {CLAUDE_PATH}")
        print(f"Command: {' '.join(cmd)}")

        try:
            # Open output file for streaming (matching agent.py pattern)
            with open(output_path, "w") as output_f:
                # Execute Claude Code and stream output to file
                result = subprocess.run(
                    cmd,
                    stdout=output_f,  # Stream directly to file
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=Path.cwd().parent.parent,  # Move up twice to get to the repo root
                    env=get_safe_subprocess_env(),  # Pass environment variables
                )

            if result.returncode != 0:
                error_msg = f"Claude Code failed with exit code {result.returncode}"
                if result.stderr:
                    error_msg += f": {result.stderr}"
                print(f"Error: {error_msg}")
                return error_msg, "[]", None

            # Parse the JSONL output
            if output_path.exists():
                return parse_jsonl_output(output_path)
            else:
                return "Claude Code completed but no output file generated", "[]", None

        except Exception as e:
            error_msg = f"Failed to execute Claude Code: {str(e)}"
            print(f"Error: {error_msg}")
            return error_msg, "[]", None


async def main(agent_id: str, prompt: str):
    """Main workflow for processing an agent prompt"""
    print(f"Processing prompt for agent {agent_id}")
    print(f"Prompt: {prompt}")

    # Get agent from database
    agent = await get_agent_from_db(agent_id)
    if not agent:
        print(f"Error: Agent {agent_id} not found in database")
        sys.exit(1)

    # Log session ID status
    if agent.cc_session_id:
        print(f"Found existing Claude session ID: {agent.cc_session_id}")
        print(f"Will resume conversation with {len(agent.conversation)} previous messages")
    else:
        print(f"No Claude session ID found. Will create new session.")

    try:
        # Execute Claude Code - pass existing session ID if available
        result_message, full_output, session_id = await execute_claude_code(
            prompt, agent_id, agent.cc_session_id
        )

        # If this was the first prompt and we got a session ID, store it
        if session_id and not agent.cc_session_id:
            print(f"Storing new Claude session ID: {session_id}")
            agent.cc_session_id = session_id
        elif session_id and agent.cc_session_id and session_id != agent.cc_session_id:
            print(f"Warning: Session ID changed from {agent.cc_session_id} to {session_id}")
            agent.cc_session_id = session_id

        # Add agent response to conversation
        agent_message = AEAMessage(
            who="agent", content=result_message, created=datetime.now().isoformat()
        )
        agent.conversation.append(agent_message)

        # Update agent state and output
        agent.full_output = full_output
        agent.state = "idle"
        agent.updated_at = datetime.now()

        # Save to database
        await update_agent_in_db(agent)
        print(f"Successfully updated agent {agent_id} with response")

    except Exception as e:
        print(f"Error processing prompt: {str(e)}")

        # Update agent to error state
        agent.state = "errored"
        agent.updated_at = datetime.now()

        # Add error message to conversation
        error_message = AEAMessage(
            who="agent", content=f"Error: {str(e)}", created=datetime.now().isoformat()
        )
        agent.conversation.append(error_message)

        await update_agent_in_db(agent)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: adw_aea_patch.py <agent_id> <prompt>")
        sys.exit(1)

    agent_id = sys.argv[1]
    prompt = sys.argv[2]

    asyncio.run(main(agent_id, prompt))
