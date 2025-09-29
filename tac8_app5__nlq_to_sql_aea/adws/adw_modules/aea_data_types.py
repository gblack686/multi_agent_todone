#!/usr/bin/env python3
"""
AEA (Agent Embedded Application) Data Types
Data models for the AEA system using Pydantic
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Literal, Optional

class AEAMessage(BaseModel):
    """Single message in an agent conversation"""
    who: Literal['user', 'agent']
    content: str
    created: str  # ISO format timestamp string

class AEAAgent(BaseModel):
    """Agent model representing a Claude Code session"""
    id: Optional[int] = None
    agent_id: str  # Our internal agent ID (aea_xxx)
    agent_name: Optional[str] = None  # AI-generated name for the agent
    adw_id: str    # ADW workflow ID
    cc_session_id: Optional[str] = None  # Claude Code session ID (set after first prompt)
    conversation: List[AEAMessage] = Field(default_factory=list)
    full_output: Optional[str] = None  # Complete raw_output.json from agent
    state: Literal['idle', 'working', 'errored', 'archived'] = 'idle'
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    archived: bool = False

class AEAPromptRequest(BaseModel):
    """Request to send a prompt to an agent"""
    agent_id: str
    prompt: str

class AEAPromptResponse(BaseModel):
    """Response after sending prompt to agent"""
    success: bool
    agent: AEAAgent
    error: Optional[str] = None

class AEANewAgentResponse(BaseModel):
    """Response when creating a new agent"""
    agent: AEAAgent

class AEAServerStatus(BaseModel):
    """Server health check response"""
    running: bool
    version: Optional[str] = None

class AEAEndAgentRequest(BaseModel):
    """Request to archive/end an agent session"""
    agent_id: str