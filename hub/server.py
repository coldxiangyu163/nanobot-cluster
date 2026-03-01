"""Hub Server — FastAPI service for agent cluster management."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from models import AgentInfo, AgentRecord, HeartbeatPayload, MessagePayload, TaskPayload
from hub.registry import Registry
from hub.router import MessageRouter

registry = Registry()
router = MessageRouter()
tasks: dict[str, TaskPayload] = {}  # task_id -> task


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown."""
    print(f"\n\U0001f916 Nanobot Cluster Hub running on port {PORT}")
    print(f"   Dashboard: http://localhost:{PORT}")
    print(f"   Agents registered: {len(registry.list_all())}\n")
    yield


PORT = int(os.environ.get("CLUSTER_PORT", "9100"))
app = FastAPI(title="Nanobot Cluster Hub", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Dashboard ---

@app.get("/")
async def dashboard():
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Dashboard not found. Place index.html in hub/static/"}


# --- Agent Registry API ---

@app.post("/api/agents/register")
async def register_agent(info: AgentInfo) -> dict:
    record = registry.register(AgentRecord(**info.model_dump()))
    _sync_router()
    return {"ok": True, "agent": record.model_dump()}


@app.get("/api/agents")
async def list_agents() -> dict:
    agents = registry.list_all()
    return {"agents": [a.model_dump() for a in agents], "count": len(agents)}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str) -> dict:
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return {"agent": agent.model_dump()}


@app.delete("/api/agents/{agent_id}")
async def unregister_agent(agent_id: str) -> dict:
    ok = registry.unregister(agent_id)
    if not ok:
        raise HTTPException(404, f"Agent {agent_id} not found")
    _sync_router()
    return {"ok": True}


@app.post("/api/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str, payload: HeartbeatPayload) -> dict:
    record = registry.heartbeat(agent_id, payload)
    if not record:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return {"ok": True, "status": record.status}


# --- Task Dispatch API ---

@app.post("/api/agents/{agent_id}/tasks")
async def dispatch_task(agent_id: str, task: TaskPayload) -> dict:
    agent = registry.get(agent_id)
    if not agent:
        raise HTTPException(404, f"Agent {agent_id} not found")
    import uuid
    task.id = task.id or str(uuid.uuid4())[:8]
    task.assigned_to = agent_id
    tasks[task.id] = task
    return {"ok": True, "task": task.model_dump()}


@app.get("/api/tasks")
async def list_tasks() -> dict:
    return {"tasks": [t.model_dump() for t in tasks.values()], "count": len(tasks)}


# --- Message Routing API ---

@app.post("/api/messages")
async def send_message(msg: MessagePayload) -> dict:
    _sync_router()
    result = await router.route(msg)
    return {"ok": True, "result": result}


@app.get("/api/messages")
async def get_messages(limit: int = 100) -> dict:
    return {"messages": router.get_log(limit)}


# --- Helpers ---

def _sync_router():
    """Sync agent endpoints to message router."""
    agents = registry.list_all()
    endpoints = {a.id: a.endpoint for a in agents if a.id and a.endpoint}
    router.update_endpoints(endpoints)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("hub.server:app", host="0.0.0.0", port=PORT, reload=True)
