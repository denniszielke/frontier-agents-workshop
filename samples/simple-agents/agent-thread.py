# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client

import os
import asyncio
from random import randint
from typing import Annotated

from agent_framework import AgentSession, Agent, InMemoryHistoryProvider
from pydantic import Field

from dotenv import load_dotenv

load_dotenv()

"""
OpenAI Chat Client with Thread Management Example

This sample demonstrates thread management with OpenAI Chat Client, showing
conversation threads and message history preservation across interactions.
"""

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client=create_chat_client(completion_model_name)

medium_client=create_chat_client(medium_model_name)

small_client=create_chat_client(small_model_name)


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def example_with_automatic_thread_creation() -> None:
    """Example showing automatic thread creation (service-managed thread)."""
    print("=== Automatic Thread Creation Example ===")

    agent = Agent(
        client=completion_client,
        instructions="You are a helpful weather agent.",
        tools=get_weather,
    )

    # First conversation - no session provided, will be created automatically
    query1 = "What's the weather like in Seattle?"
    print(f"User: {query1}")
    result1 = await agent.run(query1)
    print(f"Agent: {result1.text}")

    # Second conversation - still no session provided, will create another new session
    query2 = "What was the last city I asked about?"
    print(f"\nUser: {query2}")
    result2 = await agent.run(query2)
    print(f"Agent: {result2.text}")
    print("Note: Each call creates a separate session, so the agent doesn't remember previous context.\n")


async def example_with_thread_persistence() -> None:
    """Example showing thread persistence across multiple conversations."""
    print("=== Thread Persistence Example ===")
    print("Using the same thread across multiple conversations to maintain context.\n")

    agent = Agent(
        client=medium_client,
        instructions="You are a helpful weather agent.",
        tools=get_weather,
    )

    # Create a new session that will be reused
    session = agent.create_session()

    # First conversation
    query1 = "What's the weather like in Tokyo?"
    print(f"User: {query1}")
    result1 = await agent.run(query1, session=session)
    print(f"Agent: {result1.text}")

    # Second conversation using the same session - maintains context
    query2 = "How about London?"
    print(f"\nUser: {query2}")
    result2 = await agent.run(query2, session=session)
    print(f"Agent: {result2.text}")

    # Third conversation - agent should remember both previous cities
    query3 = "Which of the cities I asked about has better weather?"
    print(f"\nUser: {query3}")
    result3 = await agent.run(query3, session=session)
    print(f"Agent: {result3.text}")
    print("Note: The agent remembers context from previous messages in the same session.\n")


async def example_with_existing_thread_messages() -> None:
    """Example showing how to work with existing thread messages for OpenAI."""
    print("=== Existing Thread Messages Example ===")

    agent = Agent(
        client=small_client,
        instructions="You are a helpful weather agent.",
        tools=get_weather,
    )

    # Start a conversation and build up message history
    session = agent.create_session()

    query1 = "What's the weather in Paris?"
    print(f"User: {query1}")
    result1 = await agent.run(query1, session=session)
    print(f"Agent: {result1.text}")

    print("\n--- Continuing with the same session in a new agent instance ---")

    # Create a new agent instance but use the existing session with its message history
    new_agent = Agent(
        client=small_client,
        instructions="You are a helpful weather agent.",
        tools=get_weather,
    )

    # Use the same session object which contains the conversation history
    query2 = "What was the last city I asked about?"
    print(f"User: {query2}")
    result2 = await new_agent.run(query2, session=session)
    print(f"Agent: {result2.text}")
    print("Note: The agent continues the conversation using the session history.\n")

    print("\n--- Alternative: Creating a new session ---")

    # You can also create a new session
    new_session = new_agent.create_session()

    query3 = "How does the Paris weather compare to London?"
    print(f"User: {query3}")
    result3 = await new_agent.run(query3, session=new_session)
    print(f"Agent: {result3.text}")
    print("Note: This creates a new session without previous conversation history.\n")


async def main() -> None:
    print("=== OpenAI Chat Client Agent Thread Management Examples ===\n")

    await example_with_automatic_thread_creation()
    await example_with_thread_persistence()
    await example_with_existing_thread_messages()


if __name__ == "__main__":
    asyncio.run(main())