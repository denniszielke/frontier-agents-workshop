# Quickstart: Time & Weather Agent

**Feature**: Time & Weather Agent  
**Scenario**: `src/scenarios/01-hello-world-agent`

## Prerequisites

1. **Python 3.11+** installed
2. **Environment variables** configured in `.env` file at repository root:
   ```
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key
   COMPLETION_DEPLOYMENT_NAME=gpt-4o
   MEDIUM_DEPLOYMENT_MODEL_NAME=gpt-4o-mini
   SMALL_DEPLOYMENT_MODEL_NAME=gpt-4o-mini
   ```
3. **Dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Agent

### Step 1: Start MCP Servers

Open two terminal windows and start both MCP servers:

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

Wait for both servers to show "Uvicorn running on..." messages.

### Step 2: Run the Agent

**Terminal 3 - Agent**:
```bash
cd src/scenarios/01-hello-world-agent
python time_weather_agent.py
```

### Step 3: Test Conversations

Try these queries in sequence to test all capabilities:

```
User: I am currently in London
Agent: [Acknowledges location]

User: What is the weather now here?
Agent: [Returns London weather with time-of-day context]

User: What time is it for me right now?
Agent: [Returns current London time]

User: I moved to Berlin, what is the weather like today?
Agent: [Updates location, returns Berlin weather]

User: Can you remind me where I said I am based?
Agent: [Recalls Berlin from conversation history]
```

### Step 4: View Agent Traces (Optional)

To see detailed agent activities and tool calls:

**Terminal 4 - Dev UI**:
```bash
agent-framework-devui
```

Then open `http://localhost:8080` in your browser.

## Troubleshooting

### MCP Server Connection Errors

```
Error: Could not connect to MCP server
```

**Solution**: Ensure MCP servers are running before starting the agent:
- User server should be accessible at `http://localhost:8002/mcp`
- Weather server should be accessible at `http://localhost:8001/mcp`

### Unsupported Location

```
Agent: Unsupported location. Use `list_supported_locations` to see valid options.
```

**Solution**: The weather server only supports: Seattle, New York, London, Berlin, Tokyo, Sydney

### Environment Variable Errors

```
Error: Model name is missing
```

**Solution**: Ensure `.env` file exists at repository root with required variables.

## Architecture Overview

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌─────────────────┐
│  Time & Weather │      │  AgentThread    │
│     Agent       │◄────►│  (Memory)       │
└────────┬────────┘      └─────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ User  │ │Weather│
│ MCP   │ │ MCP   │
│:8002  │ │:8004  │
└───────┘ └───────┘
```

## Files

| File | Description |
|------|-------------|
| `time_weather_agent.py` | Main agent implementation |
| `README.md` | Scenario overview and learning objectives |
| `base_agent.py` | Original placeholder (reference only) |

## Related Samples

- [basic-agent.py](../../../samples/simple-agents/basic-agent.py) - Simple tool usage
- [agent-thread.py](../../../samples/simple-agents/agent-thread.py) - Conversation memory
- [agents-using-mcp.py](../../../samples/simple-agents/agents-using-mcp.py) - MCP server integration
