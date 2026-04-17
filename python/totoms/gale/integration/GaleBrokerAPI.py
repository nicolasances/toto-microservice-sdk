import os
from dataclasses import dataclass

import requests

from totoms.TotoLogger import TotoLogger
from totoms.auth.TotoToken import new_toto_service_token
from totoms.gale.model.AgentConversationMessage import AgentConversationMessage
from totoms.gale.model.AgentEndpoint import AgentEndpoint
from totoms.gale.model.AgentManifest import AgentManifest
from totoms.model.TotoConfig import TotoControllerConfig


@dataclass
class RegisterAgentRequest:
    agent_manifest: AgentManifest
    endpoint: AgentEndpoint


@dataclass
class RegisterAgentResponse:
    modified_count: int

    @staticmethod
    def from_http_response(data: dict) -> "RegisterAgentResponse":
        return RegisterAgentResponse(modified_count=data.get("modifiedCount", 0))


class GaleBrokerAPI:
    """Client for the Gale Broker API."""

    def __init__(self, config: TotoControllerConfig):
        self.config = config
        self.logger = TotoLogger.get_instance()

        gale_broker_url = os.getenv("GALE_BROKER_URL")
        if not gale_broker_url:
            raise RuntimeError(
                "GALE_BROKER_URL environment variable is not set, required for Gale integration"
            )
        self.gale_broker_url = gale_broker_url

    def register_agent(self, request: RegisterAgentRequest) -> RegisterAgentResponse:
        """Register an agent with the Gale Broker catalog."""
        token = new_toto_service_token(self.config)

        response = requests.put(
            f"{self.gale_broker_url}/catalog/agents",
            headers={
                "x-correlation-id": "Gale-registerAgent",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={
                "agentDefinition": {
                    "name": request.agent_manifest.human_friendly_name,
                    "agentId": request.agent_manifest.agent_id,
                    "agentType": request.agent_manifest.agent_type,
                    "description": request.agent_manifest.description,
                    "endpoint": {
                        "baseURL": request.endpoint.base_url,
                        "messagesPath": request.endpoint.messages_path,
                        "infoPath": request.endpoint.info_path,
                    },
                }
            },
        )

        response.raise_for_status()
        return RegisterAgentResponse.from_http_response(response.json())

    def post_conversation_message(self, msg: AgentConversationMessage) -> None:
        """Post a message to a conversation via the Gale Broker."""
        token = new_toto_service_token(self.config)

        response = requests.post(
            f"{self.gale_broker_url}/messages",
            headers={
                "x-correlation-id": msg.conversation_id or "",
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json=msg.to_dict(),
        )

        response.raise_for_status()
