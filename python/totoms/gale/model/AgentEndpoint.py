from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from totoms.gale.model.AgentManifest import AgentManifest


@dataclass
class AgentEndpoint:
    """Endpoint configuration for a Gale agent."""
    base_url: str
    messages_path: str
    info_path: str
    execution_path: Optional[str] = None

    @staticmethod
    def from_agent_manifest(manifest: AgentManifest, base_path: Optional[str] = None) -> AgentEndpoint:
        """Create an AgentEndpoint from an AgentManifest.

        Requires the SERVICE_BASE_URL environment variable to be set.

        Args:
            manifest: The agent manifest.
            base_path: Optional base path of the microservice (e.g. "/suppieagent").
                       When provided it is prepended to the agent paths so that Gale
                       Broker constructs the correct URL.
        """
        base_url = os.getenv("SERVICE_BASE_URL")

        if not base_url:
            raise RuntimeError(
                "SERVICE_BASE_URL environment variable is not set, but is REQUIRED for Gale integration. "
                "This should be the base URL (without base path) of your microservice."
            )

        prefix = base_path.rstrip("/") if base_path else ""

        return AgentEndpoint(
            base_url=base_url,
            messages_path=f"{prefix}/agents/{manifest.agent_id}/messages",
            info_path=f"{prefix}/agents/{manifest.agent_id}/info",
        )
