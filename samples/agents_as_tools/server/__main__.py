"""Local Weather Agent MCP Server

This module exposes the local `WeatherAgent` via MCP tools, without any
Azure AI Agent Service dependency. A static list of supported agents is
initialized on startup and used to route queries. The `weather-agent`
is the default agent.
"""

import sys
import logging
from typing import Dict
import asyncio
import uvicorn
from dotenv import load_dotenv
from fastmcp import FastMCP

from samples.agents_as_tools.server.weather_agent import WeatherAgent
from samples.agents_as_tools.server.news_agent import NewsAgent

from agent_framework import (
    AgentResponse,
    AgentResponseUpdate,
    AgentSession,
    BaseAgent,
    Message,
    Role,
    Content,
)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("local_agent_mcp")


load_dotenv()


# --- Static agent registry -------------------------------------------------

class AgentInfo:
    """Simple container for locally-available agents."""

    def __init__(self, agent_id: str, name: str, description: str, agent: BaseAgent):
        self.id = agent_id
        self.name = name
        self.description = description
        self.agent = agent


# Initialize a static list/dict of supported agents at startup.
SUPPORTED_AGENTS: Dict[str, AgentInfo] = {}
DEFAULT_AGENT_ID: str | None = None


def initialize_agents() -> None:
    """Initialize the local agent registry.

    Currently this just wires up a single `WeatherAgent` as the default.
    """

    global SUPPORTED_AGENTS, DEFAULT_AGENT_ID

    weather_agent = WeatherAgent(
        name="WeatherBot",
        description="An agent that can answer weather questions using a tool",
    )

    agent_id = "weather-agent"
    SUPPORTED_AGENTS[agent_id] = AgentInfo(
        agent_id=agent_id,
        name=weather_agent.name,
        description=weather_agent.description or "Weather agent",
        agent=weather_agent,
    )

    news_agent = NewsAgent(
        name="NewsBot",
        description="An agent that can fetch and summarize Hacker News stories",
    )
    agent_id = "news-agent"
    SUPPORTED_AGENTS[agent_id] = AgentInfo(
        agent_id=agent_id,
        name=news_agent.name,
        description=news_agent.description or "News agent",
        agent=news_agent,
    )

    DEFAULT_AGENT_ID = "weather-agent"


initialize_agents()


# Initialize MCP and server
mcp = FastMCP(
    "local-agent-server",
    "1.0.0",
)

sse_app = mcp.http_app(path="/sse", transport="sse")

def _get_local_agent(agent_id: str) -> AgentInfo | None:
    """Fetch an agent from the static registry."""

    return SUPPORTED_AGENTS.get(agent_id)

@mcp.resource("config://version")
def get_version() -> dict: 
    return {
        "version": "1.2.0",
        "features": ["tools", "resources"],
    }

@mcp.tool()
async def connect_agent(agent_id: str, query: str) -> str:
    """Connect to a specific locally registered agent by ID."""

    logger.info("connect_agent called", extra={"agent_id": agent_id, "query": query})

    agent_info = _get_local_agent(agent_id)
    if agent_info is None:
        logger.warning("connect_agent unknown agent id", extra={"agent_id": agent_id})
        return f"Error: Unknown agent id '{agent_id}'."

    # For now, we just run the agent without threading; could be extended.
    try:
        result = await agent_info.agent.run(query)
        text = result.text or "(no response)"
        response = f"## Response from {agent_info.name}\n\n{text}"
        logger.info("connect_agent succeeded", extra={"agent_id": agent_id})
        return response
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Agent execution failed", extra={"agent_id": agent_id})
        return f"Error running agent '{agent_id}': {exc}"


@mcp.tool()
async def query_default_agent(query: str) -> str:
    """Send a query to the default local agent (WeatherAgent)."""

    logger.info("query_default_agent called", extra={"query": query, "default_agent_id": DEFAULT_AGENT_ID})

    if not DEFAULT_AGENT_ID:
        logger.error("No default local agent configured")
        return "Error: No default local agent configured."

    agent_info = _get_local_agent(DEFAULT_AGENT_ID)
    if agent_info is None:
        logger.error("Default agent is not available", extra={"default_agent_id": DEFAULT_AGENT_ID})
        return "Error: Default agent is not available."

    try:
        result = await agent_info.agent.run(query)
        text = result.text or "(no response)"
        response = f"## Response from Default Agent ({agent_info.name})\n\n{text}"
        logger.info("query_default_agent succeeded", extra={"default_agent_id": DEFAULT_AGENT_ID})
        return response
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Default agent execution failed", extra={"default_agent_id": DEFAULT_AGENT_ID})
        return f"Error running default agent: {exc}"


@mcp.tool()
async def list_agents() -> str:
    """List available local agents."""

    logger.info("list_agents called")

    if not SUPPORTED_AGENTS:
        logger.warning("list_agents called but no agents are registered")
        return "No local agents are registered."

    result = "## Available Local Agents\n\n"
    for agent_id, info in SUPPORTED_AGENTS.items():
        result += f"- **{info.name}**: `{agent_id}` - {info.description}\n"

    if DEFAULT_AGENT_ID:
        result += f"\n**Default Agent ID**: `{DEFAULT_AGENT_ID}`"

    logger.info(
        "list_agents succeeded",
        extra={
            "agent_ids": list(SUPPORTED_AGENTS.keys()),
            "default_agent_id": DEFAULT_AGENT_ID,
        },
    )

    return result

async def check_mcp(mcp: FastMCP):
    # List the components that were created
    tools = await mcp.get_tools()
    resources = await mcp.get_resources()
    templates = await mcp.get_resource_templates()
    
    print(
        f"{len(tools)} Tool(s): {', '.join([t.name for t in tools.values()])}"
    )
    print(
        f"{len(resources)} Resource(s): {', '.join([r.name for r in resources.values()])}"
    )
    print(
        f"{len(templates)} Resource Template(s): {', '.join([t.name for t in templates.values()])}"
    )
    
    return mcp

if __name__ == "__main__":
    try:
        asyncio.run(check_mcp(mcp))
        uvicorn.run(sse_app, host="0.0.0.0", port=8001)

    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Cleaning up...")
    except Exception as exc:
        print(f"An error occurred: {exc}")