"""Agent Client — registers with hub and maintains heartbeat."""
from __future__ import annotations

import argparse
import asyncio
import signal
import sys
import time

import httpx

from agent.config import load_config, AgentConfig

HEARTBEAT_INTERVAL = 30  # seconds


class AgentClient:
    """Manages agent lifecycle: register, heartbeat, unregister."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_id: str | None = None
        self._running = True

    async def start(self) -> None:
        """Register and start heartbeat loop."""
        await self._register()
        if not self.agent_id:
            print("[ERROR] Registration failed. Exiting.")
            return

        print(f"[OK] Agent '{self.config.name}' registered as {self.agent_id}")
        print(f"     Hub: {self.config.hub}")
        print(f"     Focus: {self.config.focus}")
        print(f"     Heartbeat every {HEARTBEAT_INTERVAL}s\n")

        # Handle graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        while self._running:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if self._running:
                await self._heartbeat()

    async def stop(self) -> None:
        """Unregister and stop."""
        self._running = False
        if self.agent_id:
            await self._unregister()
            print(f"\n[BYE] Agent {self.agent_id} unregistered.")
        sys.exit(0)

    async def _register(self) -> None:
        """Register with hub. Retry on failure."""
        url = f"{self.config.hub}/api/agents/register"
        payload = {
            "name": self.config.name,
            "capabilities": self.config.capabilities,
            "focus": self.config.focus,
            "endpoint": self.config.endpoint,
        }
        for attempt in range(5):
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        self.agent_id = data["agent"]["id"]
                        return
            except Exception as e:
                wait = 2 ** attempt
                print(f"[RETRY] Hub unreachable ({e}), retrying in {wait}s...")
                await asyncio.sleep(wait)
        print("[FAIL] Could not register after 5 attempts.")

    async def _heartbeat(self) -> None:
        """Send heartbeat to hub."""
        url = f"{self.config.hub}/api/agents/{self.agent_id}/heartbeat"
        payload = {"status": "idle", "current_tasks": 0}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    print(f"  ❤️ heartbeat ok ({time.strftime('%H:%M:%S')})")
                else:
                    print(f"  ⚠️ heartbeat failed: {resp.status_code}")
        except Exception as e:
            print(f"  ⚠️ heartbeat error: {e}")

    async def _unregister(self) -> None:
        """Unregister from hub."""
        url = f"{self.config.hub}/api/agents/{self.agent_id}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.delete(url)
        except Exception:
            pass


async def main():
    parser = argparse.ArgumentParser(description="Nanobot Agent Client")
    parser.add_argument("--config", "-c", default="agent.yaml", help="Path to agent.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    client = AgentClient(config)
    await client.start()


if __name__ == "__main__":
    asyncio.run(main())
