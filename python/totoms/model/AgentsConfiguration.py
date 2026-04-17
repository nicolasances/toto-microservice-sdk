from dataclasses import dataclass, field
from typing import List, Type

from totoms.gale.agent.GaleAgent import GaleAgent


@dataclass
class AgentsConfiguration:
    """Configuration for registering Gale agents with the microservice."""
    agents: List[Type[GaleAgent]] = field(default_factory=list)
