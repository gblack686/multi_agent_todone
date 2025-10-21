#!/usr/bin/env -S uv run
# /// script
# dependencies = ["fastapi", "uvicorn", "python-dotenv", "pydantic", "aiosqlite"]
# ///

"""
AEA (Agent Embedded Application) Server
FastAPI server for managing AI agent sessions

AGENT SESSION MANAGEMENT:
- Each agent has a unique agent_id (e.g., aea_123abc456def)
- Each agent may have a cc_session_id (Claude's session ID)
- On first prompt: cc_session_id is None, Claude creates one, we store it
- On subsequent prompts: cc_session_id exists, we pass it to Claude with --resume
- On app refresh: Client reconnects using existing agent_id
- Database persists: agent_id, cc_session_id, conversation history

CRITICAL FLOW:
1. Client refresh → main.ts fetches agent_ids → reconnectToAgent(agent_id)
2. New prompt → prompt_agent → get_agent_from_db → launch subprocess with agent_id
3. Subprocess → get_agent_from_db → use cc_session_id with --resume if exists
"""

import asyncio
import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
import sys
import os
import tempfile

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import aiosqlite
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from adw_modules.aea_data_types import (
    AEAAgent,
    AEAMessage,
    AEAPromptRequest,
    AEAPromptResponse,
    AEANewAgentResponse,
    AEAServerStatus,
    AEAEndAgentRequest,
)

# Database setup
DB_PATH = Path(__file__).parent.parent / "adw_data" / "aea_agents.db"

# FastAPI app
app = FastAPI(title="AEA Server", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],  # Frontend dev servers
    allow_methods=["*"],
    allow_headers=["*"],
)

# Server configuration
PORT = 8743  # Obscure port to avoid conflicts
HOST = "0.0.0.0"

# Active processes tracking
active_processes = {}

# Background tasks to prevent garbage collection
background_tasks = set()

# Get Claude Code CLI path from environment
CLAUDE_PATH = os.getenv("CLAUDE_CODE_PATH", "claude")


async def init_db():
    """Initialize the SQLite database"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS aea_agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL UNIQUE,
                agent_name TEXT,
                adw_id TEXT NOT NULL,
                cc_session_id TEXT,
                conversation TEXT NOT NULL DEFAULT '[]',
                full_output TEXT,
                state TEXT DEFAULT 'idle',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                archived BOOLEAN DEFAULT FALSE
            )
        """
        )

        await db.commit()


def generate_agent_id() -> str:
    """Generate a unique agent ID"""
    return f"aea_{uuid.uuid4().hex[:12]}"


def generate_adw_id() -> str:
    """Generate a unique ADW workflow ID"""
    return f"adw_{uuid.uuid4().hex[:8]}"


async def generate_agent_name() -> str:
    """
    Generate a creative one-word name for the agent using Claude haiku
    
    Returns:
        str: agent_name
    """
    prompt = "Generate a single creative one-word name for an AI assistant. Just respond with the name, nothing else. Examples: Zephyr, Nova, Echo, Sage, Pixel, Nexus, Atlas, Cosmo, Indigo, Phoenix, Vortex, Nimbus, Prism, Catalyst, Zenith, Quantum, Cipher, Blaze, Flux, Nebula, Spark, Glitch, Rune, Axiom, Byte. One weird fun name. Return only a single word."
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "name_output.jsonl"
            
            # Build Claude command with haiku model
            cmd = [CLAUDE_PATH, "-p", prompt]
            cmd.extend(["--model", "haiku"])
            cmd.extend(["--output-format", "stream-json"])
            cmd.append("--verbose")  # Required for stream-json
            cmd.append("--dangerously-skip-permissions")
            
            print("Generating agent name with Claude haiku...")
            
            # Execute Claude Code
            with open(output_path, "w") as output_f:
                result = subprocess.run(
                    cmd,
                    stdout=output_f,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=Path.cwd(),
                    timeout=10  # Quick timeout for name generation
                )
            
            if result.returncode != 0:
                print(f"Failed to generate name: {result.stderr}")
                # Fallback to a default name
                return "Agent"
            
            # Parse output to get name
            if output_path.exists():
                with open(output_path, "r") as f:
                    messages = []
                    
                    for line in f:
                        if line.strip():
                            try:
                                msg = json.loads(line)
                                messages.append(msg)
                            except json.JSONDecodeError:
                                continue
                    
                    # Find the result with the name
                    agent_name = None
                    for msg in reversed(messages):
                        if msg.get("type") == "result":
                            agent_name = msg.get("result", "").strip()
                            break
                        elif msg.get("type") == "assistant":
                            content = msg.get("message", {}).get("content", [])
                            if content and isinstance(content, list):
                                for c in content:
                                    if c.get("type") == "text":
                                        agent_name = c.get("text", "").strip()
                                        break
                    
                    if agent_name:
                        # Aggressively clean up - take first word only, remove all non-alphanumeric
                        agent_name = agent_name.strip()
                        # Split on any whitespace, punctuation, or special chars and take first part
                        import re
                        words = re.findall(r'\w+', agent_name)
                        if words:
                            agent_name = words[0]
                        else:
                            agent_name = "Agent"
                        
                        # Ensure it's alphanumeric only
                        agent_name = ''.join(c for c in agent_name if c.isalnum())
                        
                        # Capitalize first letter for consistency
                        if agent_name:
                            agent_name = agent_name[0].upper() + agent_name[1:].lower()
                        else:
                            agent_name = "Agent"
                            
                        print(f"Generated agent name: {agent_name}")
                        return agent_name
                    
            return "Agent"
            
    except Exception as e:
        print(f"Error generating agent name: {e}")
        return "Agent"


async def get_agent_from_db(agent_id: str) -> Optional[AEAAgent]:
    """Fetch agent from database - ALWAYS checks for existing agent first"""
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
                    agent_name=row["agent_name"],  # THIS WAS MISSING!
                    adw_id=row["adw_id"],
                    cc_session_id=row["cc_session_id"],
                    conversation=json.loads(row["conversation"]),
                    full_output=row["full_output"],
                    state=row["state"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    archived=bool(row["archived"]),
                )
                # Log retrieval for debugging
                print(f"Retrieved agent {agent_id} from DB:")
                print(f"  - Name: {agent.agent_name or 'Not set yet'}")
                print(f"  - Claude session ID: {agent.cc_session_id or 'None (will create new)'}")
                print(f"  - Conversation messages: {len(agent.conversation)}")
                print(f"  - State: {agent.state}")
                return agent
    print(f"Agent {agent_id} not found in database")
    return None


async def update_agent_in_db(agent: AEAAgent):
    """Update agent in database"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE aea_agents 
            SET conversation = ?, full_output = ?, state = ?, 
                updated_at = ?, archived = ?, cc_session_id = ?, agent_name = ?
            WHERE agent_id = ?
            """,
            (
                json.dumps([msg.model_dump() for msg in agent.conversation]),
                agent.full_output,
                agent.state,
                datetime.now().isoformat(),
                agent.archived,
                agent.cc_session_id,
                agent.agent_name,
                agent.agent_id,
            ),
        )
        await db.commit()


async def create_agent_in_db(agent: AEAAgent) -> AEAAgent:
    """Create new agent in database"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO aea_agents (agent_id, agent_name, adw_id, cc_session_id, conversation, state, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent.agent_id,
                agent.agent_name,
                agent.adw_id,
                agent.cc_session_id,  # Will be None initially
                json.dumps([]),
                agent.state,
                agent.created_at.isoformat(),
                agent.updated_at.isoformat(),
            ),
        )
        await db.commit()
        agent.id = cursor.lastrowid
    return agent


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await init_db()
    print(f"AEA Server initialized. Database at: {DB_PATH}")


@app.get("/aea/check_server", response_model=AEAServerStatus)
async def check_server():
    """Check if AEA server is running"""
    return AEAServerStatus(running=True, version="1.0.0")


@app.post("/aea/new_agent", response_model=AEANewAgentResponse)
async def new_agent():
    """Create a new agent session - name generated asynchronously"""
    # Create agent immediately with temporary name
    agent_id = generate_agent_id()
    agent = AEAAgent(
        agent_id=agent_id,
        agent_name=None,  # Will be set asynchronously
        adw_id=generate_adw_id(),
        cc_session_id=None,  # Will be set on first actual prompt
        conversation=[],
        state="idle",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    agent = await create_agent_in_db(agent)
    print(f"Created new agent: {agent.agent_id}")

    # Generate name asynchronously (don't wait)
    async def update_agent_name():
        try:
            name = await generate_agent_name()
            # Update agent in database with the name
            async with aiosqlite.connect(DB_PATH) as db:
                result = await db.execute(
                    "UPDATE aea_agents SET agent_name = ? WHERE agent_id = ?",
                    (name, agent_id)
                )
                await db.commit()
                print(f"Updated agent {agent_id} with name: {name} (rows affected: {result.rowcount})")
                
                # Verify the update
                cursor = await db.execute(
                    "SELECT agent_name FROM aea_agents WHERE agent_id = ?",
                    (agent_id,)
                )
                row = await cursor.fetchone()
                if row:
                    print(f"Verified: Agent {agent_id} name in DB is now: {row[0]}")
        except Exception as e:
            print(f"Failed to update agent name: {e}")
            import traceback
            traceback.print_exc()
    
    # Start name generation in background - ensure it runs
    task = asyncio.create_task(update_agent_name())
    # Store reference to prevent garbage collection
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    return AEANewAgentResponse(agent=agent)


@app.post("/aea/prompt_agent", response_model=AEAPromptResponse)
async def prompt_agent(request: AEAPromptRequest):
    """Send prompt to agent"""
    # Get agent from database
    agent = await get_agent_from_db(request.agent_id)
    if not agent:
        raise HTTPException(
            status_code=404, detail=f"Agent {request.agent_id} not found"
        )

    # Log session continuity
    if agent.cc_session_id:
        print(f"Prompting agent {request.agent_id} with existing session {agent.cc_session_id}")
        print(f"  Conversation history: {len(agent.conversation)} messages")
    else:
        print(f"Prompting agent {request.agent_id} - will create new Claude session")

    if agent.state != "idle":
        return AEAPromptResponse(
            success=False,
            agent=agent,
            error=f"Agent is currently {agent.state}, cannot accept new prompts",
        )

    # Update agent state to working
    agent.state = "working"

    # Add user message to conversation
    user_message = AEAMessage(
        who="user", content=request.prompt, created=datetime.now().isoformat()
    )
    agent.conversation.append(user_message)
    agent.updated_at = datetime.now()

    # Update database
    await update_agent_in_db(agent)

    # Launch subprocess to process the prompt
    try:
        # Create the adw_aea_patch.py script path
        patch_script = Path(__file__).parent.parent / "adw_aea_patch.py"

        # Log what we're passing to the subprocess
        print(f"Launching subprocess for agent {request.agent_id}:")
        print(f"  - Agent has session ID: {agent.cc_session_id or 'None'}")
        print(f"  - Conversation history: {len(agent.conversation)} messages")
        print(f"  - Prompt: {request.prompt[:50]}..." if len(request.prompt) > 50 else f"  - Prompt: {request.prompt}")

        # Launch subprocess in background - it will fetch agent from DB using agent_id
        process = subprocess.Popen(
            ["uv", "run", str(patch_script), request.agent_id, request.prompt],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent.parent,  # Run from project root
        )

        # Track the process
        active_processes[request.agent_id] = process

        print(f"  - Subprocess PID: {process.pid}")

        return AEAPromptResponse(success=True, agent=agent)

    except Exception as e:
        # If subprocess launch fails, revert state
        agent.state = "errored"
        await update_agent_in_db(agent)
        return AEAPromptResponse(
            success=False,
            agent=agent,
            error=f"Failed to launch agent process: {str(e)}",
        )


@app.get("/aea/get_agent_ids")
async def get_agent_ids():
    """Get list of all non-archived agent IDs"""
    agent_ids = []
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT agent_id FROM aea_agents WHERE archived = 0"
        ) as cursor:
            rows = await cursor.fetchall()
            agent_ids = [row[0] for row in rows]

    print(f"Returning {len(agent_ids)} active agent IDs")
    return agent_ids


@app.get("/aea/poll_agent_by_id", response_model=AEAAgent)
async def poll_agent_by_id(agent_id: str = Query(...)):
    """Get agent updates for polling"""
    agent = await get_agent_from_db(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Only log important session changes, not every poll
    # This reduces noise while still tracking critical state
    pass

    # Check if subprocess is still running
    if agent_id in active_processes:
        process = active_processes[agent_id]
        if process.poll() is not None:
            # Process has finished
            del active_processes[agent_id]
            # The adw_aea_patch.py script should have updated the database
            # Fetch fresh data
            agent = await get_agent_from_db(agent_id)
            print(f"Agent {agent_id} subprocess completed, refreshed from DB")

    return agent


@app.post("/aea/end_agent")
async def end_agent(request: AEAEndAgentRequest):
    """Archive agent session"""
    agent = await get_agent_from_db(request.agent_id)
    if not agent:
        raise HTTPException(
            status_code=404, detail=f"Agent {request.agent_id} not found"
        )

    # Kill subprocess if still running
    if request.agent_id in active_processes:
        process = active_processes[request.agent_id]
        if process.poll() is None:
            process.terminate()
            await asyncio.sleep(0.5)
            if process.poll() is None:
                process.kill()
        del active_processes[request.agent_id]

    # Archive the agent
    agent.archived = True
    agent.state = "archived"
    agent.updated_at = datetime.now()
    await update_agent_in_db(agent)

    print(f"Archived agent: {request.agent_id}")
    return {"success": True}


if __name__ == "__main__":
    print(f"Starting AEA Server on port {PORT}...")
    uvicorn.run(app, host=HOST, port=PORT)
