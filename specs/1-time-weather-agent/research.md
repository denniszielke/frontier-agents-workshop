# Research: Time & Weather Agent

**Feature**: Time & Weather Agent  
**Date**: 2026-01-29  
**Status**: Complete

## Research Tasks

### 1. Conversation Memory Pattern

**Question**: How to maintain conversation state across multiple turns so the agent remembers user location?

**Finding**: Use `AgentThread` with `store=True` parameter

**Evidence**: From [agent-thread.py](../../../samples/simple-agents/agent-thread.py):
```python
# Create a new thread that will be reused
thread = agent.get_new_thread()

# First conversation
result1 = await agent.run(query1, thread=thread)

# Second conversation using the same thread - maintains context
result2 = await agent.run(query2, thread=thread)
```

**Decision**: Use `AgentThread` for conversation persistence
**Rationale**: Built into Microsoft Agent Framework; proven pattern in existing samples
**Alternatives Rejected**: 
- Custom memory store: Unnecessary complexity when AgentThread handles it
- External database: Overkill for workshop demo; violates simplicity principle

---

### 2. MCP Server Connection Pattern

**Question**: How to connect the agent to the weather and user MCP servers?

**Finding**: Use `MCPStreamableHTTPTool` for HTTP-based MCP servers

**Evidence**: From [agents-using-mcp.py](../../../samples/simple-agents/agents-using-mcp.py):
```python
from agent_framework import ChatAgent, MCPStreamableHTTPTool

async with ChatAgent(
    chat_client=medium_client,
    tools=MCPStreamableHTTPTool(
        name="Weather MCP",
        url="http://localhost:8004/mcp",
    ),
) as agent:
```

**Decision**: Use `MCPStreamableHTTPTool` with HTTP URLs
**Rationale**: Both MCP servers use Streamable HTTP transport; consistent with sample patterns
**Alternatives Rejected**:
- `HostedMCPTool`: For external hosted services, not local servers
- SSE transport: Deprecated in favor of Streamable HTTP

---

### 3. Location Extraction from Conversation

**Question**: How to extract user location when they say "I am in London" or "I moved to Berlin"?

**Finding**: Rely on LLM natural language understanding via system instructions

**Evidence**: The LLM can understand conversational context. System instructions guide behavior:
```python
agent = ChatAgent(
    chat_client=client,
    instructions="""You are a helpful time and weather assistant.
    When users mention their location, remember it for future queries.
    When asked about weather or time, use the remembered location.""",
    tools=[weather_mcp, user_mcp],
)
```

**Decision**: No custom NLP/parsing - LLM handles extraction naturally
**Rationale**: Simpler implementation; LLM already excels at this; consistent with agent philosophy
**Alternatives Rejected**:
- Regex patterns: Fragile; can't handle variations like "I'm currently based in..."
- NER models: Unnecessary dependency; adds complexity

---

### 4. Time Zone Handling

**Question**: How to get current time for a user's stated location?

**Finding**: User server (`02-user-server`) already provides `get_current_time(location)` tool

**Evidence**: From [server-mcp-sse-user.py](../../../src/mcp-server/02-user-server/server-mcp-sse-user.py):
```python
@mcp.tool()
def get_current_time(location: str) -> str:
    """Get the current time in the given location. 
    Location names should be in a format like America/Seattle, Asia/Bangkok, Europe/London."""
    timezone = pytz.timezone(location)
    now = datetime.now(timezone)
    current_time = now.strftime("%I:%M:%S %p")
    return current_time
```

**Decision**: Use user server's `get_current_time` tool; agent must map city names to timezone format
**Rationale**: Tool already exists; no new implementation needed
**Alternatives Rejected**:
- Add timezone mapping to weather server: Duplicates functionality
- Custom Python function: Unnecessary when MCP tool exists

---

### 5. Weather Data Source

**Question**: How to get weather for a location?

**Finding**: Weather server (`04-weather-server`) provides `get_weather_at_location(location)` tool

**Evidence**: From [server-mcp-sse-weather.py](../../../src/mcp-server/04-weather-server/server-mcp-sse-weather.py):
```python
@mcp.tool()
def get_weather_at_location(location: str) -> str:
    """Get a static weather description for a supported location 
    based on the current local time there."""
```

**Supported Locations**: Seattle, New York, London, Berlin, Tokyo, Sydney

**Decision**: Use weather server's `get_weather_at_location` tool
**Rationale**: Provides time-of-day-aware weather; matches spec requirement FR-006
**Alternatives Rejected**:
- Live weather API: Beyond workshop scope; adds external dependency

---

### 6. MCP Server Ports

**Question**: What ports do the MCP servers run on?

**Finding**: Determined from server implementations

| Server | Default Port | Endpoint |
|--------|--------------|----------|
| User Server (02) | 8002 | `http://localhost:8002/mcp` |
| Weather Server (04) | 8004 | `http://localhost:8004/mcp` |

**Decision**: Use these default ports in agent configuration
**Rationale**: Consistent with existing server configurations

---

### 7. Dev UI Integration

**Question**: How to make agent activities visible in Agent Framework Dev UI?

**Finding**: Dev UI automatically captures traces when agent-framework-devui is installed

**Evidence**: From requirements.txt:
```
agent-framework-devui==1.0.0b251120
```

**Decision**: Install and run `agent-framework-devui` alongside agent; no code changes needed
**Rationale**: Zero-configuration observability
**Alternatives Rejected**:
- Custom logging: Dev UI provides richer visualization

---

## Summary of Decisions

| Topic | Decision | Key Rationale |
|-------|----------|---------------|
| Conversation Memory | AgentThread | Built-in; proven pattern |
| MCP Connection | MCPStreamableHTTPTool | Matches server transport |
| Location Extraction | LLM via instructions | Simpler; no custom parsing |
| Time Data | User server tool | Already exists |
| Weather Data | Weather server tool | Time-of-day aware |
| Dev UI | Install agent-framework-devui | Zero-config observability |

## Unresolved Questions

None - all technical questions answered.

## Dependencies Confirmed

- ✅ `agent-framework==1.0.0b251120` - ChatAgent, AgentThread, MCPStreamableHTTPTool
- ✅ `agent-framework-devui==1.0.0b251120` - Observability UI
- ✅ MCP servers use Streamable HTTP transport (confirmed in server code)
- ✅ Weather server supports 6 locations (London, Berlin included - matches test queries)
