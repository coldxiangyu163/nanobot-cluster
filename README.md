# 🤖 Nanobot Agent Cluster

> From single agent to agent cluster — multi-instance registry, visual dashboard, and orchestrated collaboration.

## Architecture

```
                    ┌─────────────┐
                    │  Web UI     │
                    │  Dashboard  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │      Hub (Router)       │
              │   Registry + Messages   │
              └──┬──────┬──────┬───────┘
                 │      │      │
         ┌───────┘  ┌───┘  ┌───┘
         ▼          ▼      ▼
    ┌─────────┐ ┌──────┐ ┌──────────┐
    │ Agent A  │ │Agent B│ │ Agent C  │
    │ PV专员   │ │ 资讯  │ │ 开发专员  │
    └─────────┘ └──────┘ └──────────┘
```

Star topology — hub routes all messages, agents register on startup.

## Quick Start

### 1. Start the Hub

```bash
pip install -r requirements.txt
python -m hub.server
```

Hub runs on `http://localhost:9100`. Open it for the visual dashboard.

### 2. Register an Agent

Create `agent.yaml`:

```yaml
name: pv-agent
hub: http://localhost:9100
capabilities:
  - Frontend optimization
  - GitHub Pages deployment
focus: PromptVault maintenance
```

Start the agent:

```bash
python -m agent.client --config agent.yaml
```

The agent auto-registers, sends heartbeats every 30s, and unregisters on exit.

### 3. Dashboard

Visit `http://localhost:9100` to see:
- **Topology view** — hub at center, agents around it, color-coded by status
- **Agent list** — sidebar with all registered agents and capabilities
- **Task dispatch** — click an agent, type a task, hit send
- **Live stats** — total / online / busy / offline counts

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/agents/register` | Register a new agent |
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/:id` | Get agent details |
| DELETE | `/api/agents/:id` | Unregister agent |
| POST | `/api/agents/:id/heartbeat` | Send heartbeat |
| POST | `/api/agents/:id/tasks` | Dispatch task to agent |
| GET | `/api/tasks` | List all tasks |
| POST | `/api/messages` | Route inter-agent message |
| GET | `/api/messages` | Get message log |

## Project Structure

```
nanobot-cluster/
├── hub/
│   ├── server.py          # FastAPI hub service
│   ├── registry.py        # Agent registry manager
│   ├── router.py          # Message router (star topology)
│   └── static/
│       └── index.html     # Visual dashboard (single-file)
├── agent/
│   ├── client.py          # Agent registration client + heartbeat
│   └── config.py          # agent.yaml parser
├── models.py              # Shared Pydantic data models
├── example-agent.yaml     # Example agent config
└── requirements.txt
```

## Configuration

| Env Variable | Default | Description |
|-------------|---------|-------------|
| `CLUSTER_PORT` | `9100` | Hub server port |

Agent config (`agent.yaml`):

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Agent display name |
| `hub` | ✅ | Hub URL (default: `http://localhost:9100`) |
| `capabilities` | ❌ | List of capability strings |
| `focus` | ❌ | What this agent specializes in |
| `endpoint` | ❌ | Agent's own HTTP endpoint (for receiving messages) |

## Roadmap

- [x] **P1**: Agent Registry — register / discover / heartbeat
- [x] **P2**: Visual Dashboard — topology + task dispatch
- [ ] **P3**: Inter-agent messaging — star-topology message routing
- [ ] **P4**: Smart routing — auto-assign tasks by capability matching

## License

MIT
