"""Message router — star topology, hub relays messages between agents."""
from __future__ import annotations

import time
from collections import deque
from typing import Optional

import httpx

from models import MessagePayload

MAX_LOG_SIZE = 1000
RETRY_COUNT = 3


class MessageRouter:
    """Routes messages between agents through the hub."""

    def __init__(self):
        self._log: deque[dict] = deque(maxlen=MAX_LOG_SIZE)
        self._agent_endpoints: dict[str, str] = {}  # agent_id -> endpoint url

    def update_endpoints(self, agents: dict[str, str]) -> None:
        """Update known agent endpoints from registry."""
        self._agent_endpoints = agents

    async def route(self, msg: MessagePayload) -> dict:
        """Route a message to target agent(s)."""
        entry = msg.model_dump()
        entry["delivered"] = False

        if msg.to_agent == "*":
            # broadcast
            results = []
            for aid, endpoint in self._agent_endpoints.items():
                if aid != msg.from_agent:
                    ok = await self._deliver(endpoint, msg)
                    results.append({"agent": aid, "delivered": ok})
            entry["delivered"] = any(r["delivered"] for r in results)
            entry["broadcast_results"] = results
        else:
            endpoint = self._agent_endpoints.get(msg.to_agent)
            if endpoint:
                entry["delivered"] = await self._deliver(endpoint, msg)
            else:
                entry["error"] = f"Agent {msg.to_agent} not found or no endpoint"

        self._log.append(entry)
        return entry

    async def _deliver(self, endpoint: str, msg: MessagePayload) -> bool:
        """Deliver message to agent endpoint with retries."""
        url = f"{endpoint.rstrip('/')}/api/inbox"
        for attempt in range(RETRY_COUNT):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(url, json=msg.model_dump())
                    if resp.status_code == 200:
                        return True
            except Exception:
                if attempt < RETRY_COUNT - 1:
                    await _sleep(1)
        return False

    def get_log(self, limit: int = 100) -> list[dict]:
        return list(self._log)[-limit:]


async def _sleep(seconds: float) -> None:
    import asyncio
    await asyncio.sleep(seconds)
