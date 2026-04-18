from abc import ABC, abstractmethod
from typing import Optional

from totoms.evt.TotoMessageBus import TotoMessageBus
from totoms.gale.model.AgentManifest import AgentManifest
from totoms.model.TotoConfig import TotoControllerConfig


class GaleAgent(ABC):
    """Abstract base class for Gale agents."""

    def __init__(self, message_bus: Optional[TotoMessageBus], config: TotoControllerConfig):
        self.message_bus = message_bus
        self.config = config
        self._auth_header: Optional[str] = None

    @abstractmethod
    def get_manifest(self) -> AgentManifest:
        """Return the agent's manifest describing its type and identity."""
        ...
