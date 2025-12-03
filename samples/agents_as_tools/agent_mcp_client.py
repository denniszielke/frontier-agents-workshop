# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client
import asyncio
import os

from typing import TYPE_CHECKING

from agent_framework import ChatAgent, HostedMCPTool
from dotenv import load_dotenv

load_dotenv()

"""
MCP Tool Integration Sample

This sample demonstrates how to connect to and communicate with a local MCP
server (implemented in `samples/agents_as_tools/server/__main__.py`) using
the Agent Framework `HostedMCPTool`.

It mirrors the pattern from `samples/simple-agents/agents-using-mcp.py`, but
focuses on a single, simple interaction with the local MCP server.

To run this sample:
1. Start the MCP server (in another terminal):
   uv run --env-file .env \
      python -m samples.agents_as_tools.server.__main__

2. In a separate terminal, run this client:
   uv run --env-file .env \
      python samples/agents_as_tools/agent_mcp_client.py
"""


if TYPE_CHECKING:
    from agent_framework import AgentProtocol

medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")

medium_client=create_chat_client(medium_model_name)

async def run_simple_mcp_client() -> None:
    """Connect to the local MCP server and run a multi-step conversation.

    The MCP server exposes tools such as `list_agents` and `query_default_agent`.
    This client drives multiple turns so the agent can call tools across steps.
    """

    from agent_framework import ChatMessage

    mcp_server_url = os.getenv("LOCAL_MCP_AGENT_SERVER_URL", "http://localhost:8001/sse")
    print(f"Connecting to MCP server at: {mcp_server_url}")

    chat_client = medium_client

    async with ChatAgent(
        chat_client=chat_client,
        name="LocalMCPClient",
        instructions=(
            "You are a helpful assistant that can call tools on a local "
            "MCP server exposing a set of helpful agents. When appropriate, call "
            "`query_default_agent` to answer questions."
        ),
        tools=HostedMCPTool(
            name="Local Agent MCP",
            url=mcp_server_url,
            approval_mode="never_require",
        ),
    ) as agent:
        # Maintain an explicit conversation history so the agent can reason
        # across multiple steps and perform multiple tool calls.
        messages: list[ChatMessage] = []

        def print_turn_header(step: int, user_text: str) -> None:
            print("=" * 60)
            print(f"Step {step}: User -> {user_text}")

        # Step 1: initial question
        user_query_1 = "What is the weather in New York City today?"
        print_turn_header(1, user_query_1)
        messages.append(ChatMessage(role="user", text=user_query_1))

        result = await agent.run(messages)

        # Print assistant reply
        print(f"{agent.name}:")
        for msg in result.messages:
            if msg.role == "assistant" and msg.text:
                print(msg.text)

        # Merge result messages into history for the next step
        messages.extend(result.messages)

        # Step 2: follow-up question that should reuse context and tools
        user_query_2 = "And what about tomorrow? Please use the same MCP tools."
        print_turn_header(2, user_query_2)
        messages.append(ChatMessage(role="user", text=user_query_2))

        result = await agent.run(messages)

        print(f"{agent.name} (follow-up):")
        for msg in result.messages:
            if msg.role == "assistant" and msg.text:
                print(msg.text)


async def main() -> None:
    await run_simple_mcp_client()


if __name__ == "__main__":
    asyncio.run(main())