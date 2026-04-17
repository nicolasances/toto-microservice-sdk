from dataclasses import dataclass, field
from typing import Literal, Optional


@dataclass
class StreamInfo:
    """Streaming metadata for agent messages."""
    stream_id: str
    sequence_number: int
    last: bool


@dataclass
class MessageExtras:
    """Extra metadata for agent messages."""
    subject_email: Optional[str] = None


@dataclass
class AgentConversationMessage:
    """Message exchanged between a user and a conversational agent."""
    conversation_id: str
    message_id: str
    actor: Literal["user", "agent"]
    agent_id: str
    message: str
    stream: Optional[StreamInfo] = None
    extras: Optional[MessageExtras] = None

    def to_dict(self) -> dict:
        """Serialize to a dictionary for JSON transmission."""
        result = {
            "conversationId": self.conversation_id,
            "messageId": self.message_id,
            "actor": self.actor,
            "agentId": self.agent_id,
            "message": self.message,
        }
        if self.stream:
            result["stream"] = {
                "streamId": self.stream.stream_id,
                "sequenceNumber": self.stream.sequence_number,
                "last": self.stream.last,
            }
        if self.extras:
            result["extras"] = {
                "subjectEmail": self.extras.subject_email,
            }
        return result

    @staticmethod
    def from_dict(data: dict) -> "AgentConversationMessage":
        """Deserialize from a dictionary."""
        stream = None
        if data.get("stream"):
            s = data["stream"]
            stream = StreamInfo(
                stream_id=s["streamId"],
                sequence_number=s["sequenceNumber"],
                last=s["last"],
            )

        extras = None
        if data.get("extras"):
            extras = MessageExtras(subject_email=data["extras"].get("subjectEmail"))

        return AgentConversationMessage(
            conversation_id=data["conversationId"],
            message_id=data["messageId"],
            actor=data["actor"],
            agent_id=data["agentId"],
            message=data["message"],
            stream=stream,
            extras=extras,
        )
