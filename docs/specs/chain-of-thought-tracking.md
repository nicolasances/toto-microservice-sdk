# Chain-of-Thought Tracking in Agent Conversations

## Overview

This document describes the chain-of-thought tracking capability of the Toto Microservice SDK. It covers the `AgentConversationMessage` model, the supporting types (`StreamInfo`, `MessageExtras`), the new `chainOfThought` field, and how conversational agents use these constructs to pass full LLM reasoning data through to the Gale Broker.

---

## `AgentConversationMessage`

`AgentConversationMessage` is the core message model exchanged between users and conversational agents in the Gale framework. It is defined in both the Python SDK and the Node.js SDK.

### Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `conversationId` | string | Yes | ID of the conversation this message belongs to. |
| `messageId` | string | Yes | Unique ID for this message. |
| `actor` | `"user"` \| `"agent"` | Yes | Who sent the message — the user or the agent. |
| `agentId` | string | Yes | ID of the agent this message is directed to (or from). |
| `message` | string | Yes | The plain-text content of the message. Always a string for backward compatibility with all consumers (Gale Broker SSE streams, frontends, etc.). |
| `stream` | `StreamInfo` | No | Streaming metadata, present only for messages that are part of a streamed response. |
| `extras` | `MessageExtras` | No | Optional extra metadata associated with the message. |
| `chainOfThought` | list / `any[]` | No | Raw LLM content blocks capturing the agent's full reasoning chain. See [Chain-of-Thought Field](#chain-of-thought-field). |

---

## `StreamInfo`

`StreamInfo` carries metadata for agent messages that are delivered as a stream (i.e., incrementally, token by token or chunk by chunk).

### Fields

| Field | Type | Description |
|---|---|---|
| `streamId` | string | Unique ID of the stream this message belongs to. |
| `sequenceNumber` | number / int | Sequence number of this message within the stream (1, 2, 3, …). |
| `last` | boolean | Whether this is the final message in the stream. |

`StreamInfo` is only present on messages that are part of a streaming response. Non-streaming (single-shot) agent responses do not include this field.

---

## `MessageExtras`

`MessageExtras` carries optional supplementary metadata about the conversation context.

### Fields

| Field | Type | Description |
|---|---|---|
| `subjectEmail` | string (optional) | Email address of the user who is the subject of the interaction. Useful for personalization or follow-up tasks. |

---

## Chain-of-Thought Field

### Purpose

When an agent uses an LLM with thinking or reasoning enabled (e.g., Claude extended thinking, Gemini thinking mode), the LLM returns a structured list of content blocks rather than a plain string. These blocks can include:

- `{"type": "thinking", "thinking": "..."}` — the model's internal reasoning
- `{"type": "text", "text": "..."}` — the visible text response
- `{"type": "tool_use", ...}` — tool-call invocations
- Provider-specific blocks such as signatures, citations, etc.

The `chainOfThought` field allows an agent to attach these raw content blocks to the `AgentConversationMessage` so they can be forwarded to the Gale Broker for storage and debugging — without modifying or normalizing the `message` field.

### Structure

`chainOfThought` is a raw, unmodified list of content block dicts as returned by the LLM provider. The SDK does not validate or transform its contents; the structure is entirely provider-specific.

**Example value:**

```json
[
  {
    "type": "thinking",
    "thinking": "The user is asking about their budget. I should look up their recent transactions...",
    "signature": "EqoBCkgIARgCIkDn..."
  },
  {
    "type": "text",
    "text": "Based on your recent transactions, your remaining budget for this month is €142."
  }
]
```

### When It Is Set

`chainOfThought` is optional. It is set by agents that:

1. Use an LLM with thinking/reasoning enabled, **and**
2. Wish to forward the full reasoning trace to the Gale Broker for storage or debugging.

Agents that do not use reasoning-enabled LLMs, or that do not need to forward the reasoning trace, leave `chainOfThought` unset. All existing agents continue to work unchanged.

### Backward Compatibility

The `message` field remains a plain string in all cases. Consumers that only read `message` (Gale Broker SSE streams, frontends) are unaffected by the presence or absence of `chainOfThought`.

---

## `GaleConversationalAgent` — Python SDK

The `GaleConversationalAgent` base class (in `totoms/gale/agent/GaleConversationalAgent.py`) provides the request-handling lifecycle for conversational agents in Python.

### `on_message(message: AgentConversationMessage) -> AgentConversationMessage`

Abstract method that subclasses must implement. It receives the incoming `AgentConversationMessage` from the user and must return an `AgentConversationMessage` as the agent's response.

To include chain-of-thought data in the response:

```python
async def on_message(self, message: AgentConversationMessage) -> AgentConversationMessage:
    response = await self.llm_client.call(...)  # returns content blocks
    plain_text = next(b["text"] for b in response if b["type"] == "text")

    return AgentConversationMessage(
        conversation_id=message.conversation_id,
        message_id=str(uuid4()),
        actor="agent",
        agent_id=message.agent_id,
        message=plain_text,
        chain_of_thought=response,   # full raw content blocks
    )
```

### `publish_message(message: AgentConversationMessage) -> None`

Posts an intermediate message to the conversation via the Gale Broker API. This allows agents to send incremental feedback or status updates to the user while they are processing the request, without waiting for `on_message()` to return.

---

## `GaleConversationalAgent` — Node.js SDK

The `GaleConversationalAgent` abstract class (in `src/gale/agent/GaleConversationalAgent.ts`) mirrors the Python agent model for Node.js services.

### `onMessage(message: AgentConversationMessage): Promise<AgentConversationMessage>`

Abstract method that subclasses must implement. Receives the incoming message and must resolve with the agent's response message.

To include chain-of-thought data:

```typescript
protected async onMessage(message: AgentConversationMessage): Promise<AgentConversationMessage> {
    const blocks = await this.llmClient.call(...);  // returns content blocks
    const plainText = blocks.find((b: any) => b.type === "text")?.text ?? "";

    return {
        conversationId: message.conversationId,
        messageId: uuidv4(),
        actor: "agent",
        agentId: message.agentId,
        message: plainText,
        chainOfThought: blocks,   // full raw content blocks
    };
}
```

### `publishMessage(message: AgentConversationMessage): Promise<void>`

Posts an intermediate message to the conversation via the Gale Broker API. Mirrors the Python `publish_message()` method.

---

## How Agents Use `chainOfThought` with Gale Broker

1. The agent calls its LLM and receives a list of structured content blocks.
2. The agent extracts the plain-text content for the `message` field.
3. The agent places the full, unmodified content block list in `chainOfThought`.
4. The agent returns (or publishes) the `AgentConversationMessage` with both fields set.
5. `to_dict()` / the serialized object includes `chainOfThought` only when non-null/non-empty.
6. Gale Broker receives the message and can store `chainOfThought` for debugging or audit purposes.

Consumers that only read `message` are unaffected.
