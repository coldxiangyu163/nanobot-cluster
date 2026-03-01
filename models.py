"""Shared data models for Nanobot Agent Cluster."""
from __future__ import annotations

import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    online = "online"
    idle = "idle"
    busy = "busy"
    offline = "offline"


class AgentInfo(BaseModel):
    """Agent registration payload."""
    id: Optional[str] = None
    name: str
    endpoint: Optional[str] = None
    capabilities: list[str] = []
    focus: str = ""
    status: AgentStatus = AgentStatus.idle


class AgentRecord(AgentInfo):
    """Full agent record stored in registry."""
    registered_at: float = Field(default_factory=time.time)
    last_heartbeat: float = Field(default_factory=time.time)
    current_tasks: int = 0
    last_completed: Optional[float] = None


class HeartbeatPayload(BaseModel):
    """Heartbeat data sent by agents."""
    status: AgentStatus = AgentStatus.idle
    current_tasks: int = 0
    last_completed: Optional[float] = None


class TaskPayload(BaseModel):
    """Task dispatched to an agent."""
    id: Optional[str] = None
    description: str
    from_agent: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str = "pending"
    created_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    result: Optional[str] = None


class MessagePayload(BaseModel):
    """Inter-agent message."""
    from_agent: str
    to_agent: str  # agent id or '*' for broadcast
    type: str = "notify"  # task | result | query | notify
    payload: dict = {}
    timestamp: float = Field(default_factory=time.time)
