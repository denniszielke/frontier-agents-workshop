### Scenario 1 - Your First Time & Weather Agent

Goal: In this scenario you will build your very first agent using the Microsoft Agent Framework that can answer questions about the current time and expected weather for the user’s location. You will learn how to define an agent, connect simple tools (functions) to it, and how those tools are invoked through function calling. You will also practice using an MCP server to look up user-related information and a separate MCP server to provide weather information. A key focus is to see how conversational state is maintained across multiple turns so the agent can remember details like where the user is. This scenario is relevant because most real-world agents combine memory, tools, and external services rather than just answering a single prompt.
## Quick Start

### 1. Start MCP Servers

Open two terminal windows:

**Terminal 1 - User Server** (port 8002):
```bash
cd src/mcp-server/02-user-server
python server-mcp-sse-user.py
```

**Terminal 2 - Weather Server** (port 8001):
```bash
cd src/mcp-server/04-weather-server
python server-mcp-sse-weather.py
```

### 2. Run the Agent

```bash
cd src/scenarios/01-hello-world-agent
python time_weather_agent.py
```

### 3. Try These Queries

```
You: I am currently in London
You: What is the weather now here?
You: What time is it for me right now?
You: I moved to Berlin, what is the weather like today?
You: Can you remind me where I said I am based?
```

## Files

| File | Description |
|------|-------------|
| `time_weather_agent.py` | Main agent implementation |
| `test_agent.py` | Automated test script for validation |
| `base_agent.py` | Original placeholder (reference) |

## Learning Objectives
Task:
- Start from the provided simple-agent samples and create an agent that can figure out where the user is based on the conversation.
- Enable the agent to answer what time it is for the user using the user’s location and a suitable time function or MCP server.
- Connect to a weather MCP server so the agent can describe expected weather for the user’s current location and time of day.
- Ensure the agent remembers earlier messages (for example, the user telling it where they are) and reuses that information later without asking again.
- Use the Agent Framework Dev UI to explore activities, metrics and traces to troubleshoot multi-tool agent executions.

Relevant references
- Microsoft Agent Framework Dev UI: https://pypi.org/project/agent-framework-devui/

Relevant samples:
- [`samples/simple-agents/basic-agent.py`](../../../samples/simple-agents/basic-agent.py) – basic agent that calls a tool.
- [`samples/simple-agents/agent-thread.py`](../../../samples/simple-agents/agent-thread.py) – simple agent that can manage a conversation.
- [`samples/simple-agents/agents-using-mcp.py`](../../../samples/simple-agents/agents-using-mcp.py) – simple agent that can use an MCP server.
- [`src/mcp-server/02-user-server/server-mcp-sse-user.py`](../../mcp-server/02-user-server/run-mcp-user.py) – simple MCP server that knows about users and their locations.
- [`src/mcp-server/04-weather-server/server-mcp-sse-weather.py`](../../mcp-server/04-weather-server/run-mcp-weather.py) – simple MCP server that provides time-of-day–aware weather per location.

Input queries:
- "I am currently in London"
- "What is the weather now here?"
- "What time is it for me right now?"
- "I moved to Berlin, what is the weather like today?"
- "Can you remind me where I said I am based?"

Tooling tips:
Use `basic-agent.py` to understand how to wire a simple Python function as a tool and how the agent calls it. Then look at `agent-thread.py` to see how conversations are modeled so that previous user messages are available when answering new questions. Study `agents-using-mcp.py` to see how an agent can talk to an MCP server and treat its endpoints as tools. Run the `02-user-server` and `04-weather-server` MCP servers so your agent can call them for user info and weather; you can then point your agent configuration to the `/sse` endpoints they expose. Finally, start the Agent Framework Dev UI to inspect traces and metrics while you experiment with different prompts and watch how the agent calls tools step by step.

