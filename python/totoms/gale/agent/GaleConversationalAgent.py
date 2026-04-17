from abc import abstractmethod

from fastapi import Request
from fastapi.responses import JSONResponse

from totoms.TotoLogger import TotoLogger
from totoms.TotoDelegateDecorator import extract_info, validate_request
from totoms.gale.agent.GaleAgent import GaleAgent
from totoms.gale.integration.GaleBrokerAPI import GaleBrokerAPI
from totoms.gale.model.AgentConversationMessage import AgentConversationMessage


class GaleConversationalAgent(GaleAgent):
    """Base class for conversational Gale agents.

    Subclasses must implement ``get_manifest()`` and ``on_message()``.
    """

    @abstractmethod
    async def on_message(self, message: AgentConversationMessage) -> AgentConversationMessage:
        """Handle an incoming conversation message and return a response."""
        ...

    async def publish_message(self, message: AgentConversationMessage) -> None:
        """Publish an intermediate message to the conversation via the Gale Broker."""
        logger = TotoLogger.get_instance()
        logger.log(
            message.conversation_id or "",
            f"Publishing message to conversation {message.conversation_id} for agent {message.agent_id}: {message.message}",
        )
        GaleBrokerAPI(self.config).post_conversation_message(message)

    async def on_request(self, request: Request):
        """FastAPI delegate handler for incoming agent messages.

        Validates the request, parses the body into an AgentConversationMessage,
        delegates to ``on_message()``, and returns the response as JSON.
        """
        # Validate the request (auth, correlation id, etc.)
        validation_result = await validate_request(request, self.config)

        if not validation_result.validation_passed:
            return validation_result.to_fastapi_response()

        body = await request.json()

        # Validate required fields
        for field in ("conversationId", "messageId", "agentId", "actor", "message"):
            if field not in body:
                return JSONResponse(status_code=400, content={"code": 400, "detail": f"Missing {field}"})

        incoming = AgentConversationMessage.from_dict(body)

        result = await self.on_message(incoming)

        return result.to_dict()
