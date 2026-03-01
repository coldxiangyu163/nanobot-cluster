"""Agent Registry — manages agent registration, discovery, and health."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Optional

from models import AgentRecord, AgentStatus, HeartbeatPayload

DEFAULT_DATA_DIR = Path("data/cluster")
HEARTBEAT_TIMEOUT = 90  # seconds before marking offline


class Registry:
    """In-memory agent registry with JSON file persistence."""

    def __init__(self, data_dir: Path = DEFAULT_DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._agents: dict[str, AgentRecord] = {}
        self._lock = Lock()
        self._load()

    # --- persistence ---

    @property
    def _file(self) -> Path:
        return self.data_dir / "registry.json"

    def _load(self) -> None:
        if self._file.exists():
            raw = json.loads(self._file.read_text())
            for agent_id, data in raw.items():
                self._agents[agent_id] = AgentRecord(**data)

    def _save(self) -> None:
        payload = {aid: a.model_dump() for aid, a in self._agents.items()}
        self._file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    # --- public API ---

    def register(self, info: AgentRecord) -> AgentRecord:
        """Register a new agent or re-register an existing one."""
        with self._lock:
            agent_id = info.id or str(uuid.uuid4())[:8]
            now = time.time()
            record = AgentRecord(
                id=agent_id,
                name=info.name,
                endpoint=info.endpoint,
                capabilities=info.capabilities,
                focus=info.focus,
                status=AgentStatus.online,
                registered_at=now,
                last_heartbeat=now,
                current_tasks=info.current_tasks,
            )
            self._agents[agent_id] = record
            self._save()
            return record

    def unregister(self, agent_id: str) -> bool:
        with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                self._save()
                return True
            return False

    def heartbeat(self, agent_id: str, payload: HeartbeatPayload) -> Optional[AgentRecord]:
        with self._lock:
            agent = self._agents.get(agent_id)
            if not agent:
                return None
            agent.last_heartbeat = time.time()
            agent.status = payload.status
            agent.current_tasks = payload.current_tasks
            if payload.last_completed:
                agent.last_completed = payload.last_completed
            self._save()
            return agent

    def get(self, agent_id: str) -> Optional[AgentRecord]:
        self._check_health()
        return self._agents.get(agent_id)

    def list_all(self) -> list[AgentRecord]:
        self._check_health()
        return list(self._agents.values())

    def _check_health(self) -> None:
        """Mark agents as offline if heartbeat timed out."""
        now = time.time()
        for agent in self._agents.values():
            if agent.status != AgentStatus.offline and (now - agent.last_heartbeat) > HEARTBEAT_TIMEOUT:
                agent.status = AgentStatus.offline
