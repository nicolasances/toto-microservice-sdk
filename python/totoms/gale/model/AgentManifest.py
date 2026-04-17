from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class AgentManifest:
    """Manifest describing a Gale agent."""
    agent_type: Literal["conversational", "taskExecutor"]
    agent_id: str
    human_friendly_name: str
    description: Optional[str] = None
