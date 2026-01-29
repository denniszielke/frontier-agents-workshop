# Data Model: Time & Weather Agent

**Feature**: Time & Weather Agent  
**Date**: 2026-01-29  
**Status**: Complete

## Overview

This agent uses the Microsoft Agent Framework's built-in data structures. No custom database or persistence layer is required - conversation state is maintained in-memory via `AgentThread`.

## Entities

### 1. Conversation Thread

**Description**: Represents an ongoing conversation session with a user. Maintains message history and enables the agent to recall previous context.

**Framework Class**: `agent_framework.AgentThread`

| Attribute | Type | Description |
|-----------|------|-------------|
| id | string | Unique identifier for the thread |
| messages | list[ChatMessage] | Ordered history of all messages in conversation |
| metadata | dict | Optional key-value storage for thread-level data |

**Lifecycle**:
- Created: When user starts a new conversation
- Updated: After each user message and agent response
- Persisted: In-memory for session duration
- Deleted: When conversation ends or session times out

**Relationships**:
- Contains many ChatMessages (1:N)
- Belongs to one Agent instance (N:1)

---

### 2. Chat Message

**Description**: A single message in the conversation, either from the user or the agent.

**Framework Class**: `agent_framework.ChatMessage`

| Attribute | Type | Description |
|-----------|------|-------------|
| role | string | "user", "assistant", or "system" |
| text | string | Plain text content of the message |
| contents | list[Content] | Rich content including tool calls/results |
| timestamp | datetime | When message was created |

**Message Types**:
- **User Message**: Contains user's natural language input (e.g., "I am in London")
- **Assistant Message**: Agent's response text and any tool calls made
- **System Message**: Instructions that shape agent behavior (not visible to user)

---

### 3. Tool Call

**Description**: A record of the agent invoking an MCP server tool during response generation.

**Framework Class**: `agent_framework.FunctionCall` (within ChatMessage contents)

| Attribute | Type | Description |
|-----------|------|-------------|
| id | string | Unique identifier for this tool call |
| name | string | Name of the tool (e.g., "get_weather_at_location") |
| arguments | dict | Parameters passed to the tool |

**Tool Call Result** (returned after execution):

| Attribute | Type | Description |
|-----------|------|-------------|
| call_id | string | References the original tool call |
| result | string | Tool's return value |
| error | string | Error message if tool failed |

---

### 4. User Location (Implicit)

**Description**: The user's stated location is not stored as a separate entity - it exists within the conversation history and is extracted by the LLM when needed.

**How It Works**:
1. User says "I am in London"
2. Message stored in AgentThread
3. Later query: "What's the weather here?"
4. LLM reviews thread history, finds "London", calls weather tool with "London"

**Why No Explicit Storage**:
- AgentThread already maintains full conversation history
- LLM excels at extracting context from conversation
- Simpler design; fewer moving parts
- Consistent with agent-first architecture

---

## Entity Relationships Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                      AgentThread                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ id: "thread-abc123"                                 │    │
│  │                                                     │    │
│  │ messages: [                                         │    │
│  │   ┌───────────────────────────────────────────┐    │    │
│  │   │ ChatMessage (system)                      │    │    │
│  │   │ role: "system"                            │    │    │
│  │   │ text: "You are a time/weather assistant"  │    │    │
│  │   └───────────────────────────────────────────┘    │    │
│  │   ┌───────────────────────────────────────────┐    │    │
│  │   │ ChatMessage (user)                        │    │    │
│  │   │ role: "user"                              │    │    │
│  │   │ text: "I am currently in London"          │    │    │
│  │   └───────────────────────────────────────────┘    │    │
│  │   ┌───────────────────────────────────────────┐    │    │
│  │   │ ChatMessage (assistant)                   │    │    │
│  │   │ role: "assistant"                         │    │    │
│  │   │ text: "Got it! I'll remember you're..."   │    │    │
│  │   └───────────────────────────────────────────┘    │    │
│  │   ┌───────────────────────────────────────────┐    │    │
│  │   │ ChatMessage (user)                        │    │    │
│  │   │ role: "user"                              │    │    │
│  │   │ text: "What is the weather now here?"     │    │    │
│  │   └───────────────────────────────────────────┘    │    │
│  │   ┌───────────────────────────────────────────┐    │    │
│  │   │ ChatMessage (assistant with tool call)    │    │    │
│  │   │ role: "assistant"                         │    │    │
│  │   │ contents: [                               │    │    │
│  │   │   FunctionCall {                          │    │    │
│  │   │     name: "get_weather_at_location"       │    │    │
│  │   │     arguments: {"location": "London"}     │    │    │
│  │   │   }                                       │    │    │
│  │   │ ]                                         │    │    │
│  │   │ text: "The weather in London is..."       │    │    │
│  │   └───────────────────────────────────────────┘    │    │
│  │ ]                                                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## State Transitions

### Conversation State

```text
┌──────────────┐
│  New Thread  │
│  (no history)│
└──────┬───────┘
       │ User sends message
       ▼
┌──────────────┐
│   Active     │◄────────────────┐
│  (has msgs)  │                 │
└──────┬───────┘                 │
       │ Agent responds          │ User sends
       │ (may call tools)        │ new message
       ▼                         │
┌──────────────┐                 │
│  Responded   │─────────────────┘
│  (awaiting)  │
└──────────────┘
```

### Location Context State (Implicit in Thread)

```text
┌─────────────────┐
│ Location Unknown│
│ (no mention yet)│
└────────┬────────┘
         │ User mentions location
         │ "I am in London"
         ▼
┌─────────────────┐
│ Location Known  │◄─────────────┐
│ (London)        │              │
└────────┬────────┘              │
         │ User says             │
         │ "I moved to Berlin"   │
         ▼                       │
┌─────────────────┐              │
│ Location Updated│──────────────┘
│ (Berlin)        │
└─────────────────┘
```

## Validation Rules

### Message Validation

| Rule | Description |
|------|-------------|
| Non-empty text | User messages must contain text |
| Valid role | Role must be "user", "assistant", or "system" |
| Tool call format | Tool calls must have name and valid JSON arguments |

### Location Validation (via Weather Server)

| Rule | Description |
|------|-------------|
| Supported location | Weather server supports: Seattle, New York, London, Berlin, Tokyo, Sydney |
| Graceful fallback | Unsupported locations return helpful error message |

### Time Zone Validation (via User Server)

| Rule | Description |
|------|-------------|
| Valid timezone format | Must be IANA format (e.g., "Europe/London") |
| City mapping | Agent instructions guide LLM to map cities to timezones |

## No Database Required

This design intentionally avoids persistent storage:

- **Conversation history**: Maintained in `AgentThread` (in-memory)
- **User location**: Extracted from conversation history by LLM
- **Tool results**: Passed through and included in assistant messages

This approach aligns with:
- Constitution Principle IV (Simple, Readable Codebases)
- Workshop focus on agent patterns, not data persistence
- Existing sample patterns that use in-memory state
