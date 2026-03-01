"""Agent config loader — reads agent.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel


class AgentConfig(BaseModel):
    name: str
    hub: str = "http://localhost:9100"
    capabilities: list[str] = []
    focus: str = ""
    endpoint: Optional[str] = None


def load_config(path: str | Path = "agent.yaml") -> AgentConfig:
    """Load agent configuration from YAML file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config file not found: {p}")
    data = yaml.safe_load(p.read_text())
    return AgentConfig(**data)
