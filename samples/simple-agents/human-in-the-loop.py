# Copyright (c) Microsoft. All rights reserved.

import sys
from pathlib import Path
from random import randrange
from typing import Annotated, Any

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client

import os
import asyncio
from random import randint
from typing import Annotated
from agent_framework import AgentResponse, Agent, Message, tool
from agent_framework import Content
from dotenv import load_dotenv

load_dotenv()

"""
Demonstration of a tool with approvals.

This sample demonstrates using AI functions with user approval workflows.
It shows how to handle function call approvals without using threads.
"""

conditions = ["sunny", "cloudy", "raining", "snowing", "clear"]

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client=create_chat_client(completion_model_name)

medium_client=create_chat_client(medium_model_name)

small_client=create_chat_client(small_model_name)

# NOTE: approval_mode="never_require" is for sample brevity. Use "always_require" in production; see samples/getting_started/tools/function_tool_with_approval.py and samples/getting_started/tools/function_tool_with_approval_and_threads.py.
@tool(approval_mode="never_require")
def get_weather(location: Annotated[str, "The city and state, e.g. San Francisco, CA"]) -> str:
    """Get the current weather for a given location."""
    # Simulate weather data
    return f"The weather in {location} is {conditions[randrange(0, len(conditions))]} and {randrange(-10, 30)}°C."


# Define a simple weather tool that requires approval
@tool(approval_mode="always_require")
def get_weather_detail(location: Annotated[str, "The city and state, e.g. San Francisco, CA"]) -> str:
    """Get the current weather for a given location."""
    # Simulate weather data
    return (
        f"The weather in {location} is {conditions[randrange(0, len(conditions))]} and {randrange(-10, 30)}°C, "
        "with a humidity of 88%. "
        f"Tomorrow will be {conditions[randrange(0, len(conditions))]} with a high of {randrange(-10, 30)}°C."
    )


async def handle_approvals(query: str, agent: "Agent") -> AgentResponse:
    """Handle function call approvals.

    When we don't have a thread, we need to ensure we include the original query,
    the approval request, and the approval response in each iteration.
    """
    result = await agent.run(query)
    while len(result.user_input_requests) > 0:
        # Start with the original query
        new_inputs: list[Any] = [query]

        for user_input_needed in result.user_input_requests:
            print(f"\n[DEBUG] Type of user_input_needed: {type(user_input_needed)}")
            print(f"[DEBUG] Dir: {dir(user_input_needed)}")
            print(
                f"\nUser Input Request for function from {agent.name}:"
                f"\n  Function: {user_input_needed.function_call.name}"
                f"\n  Arguments: {user_input_needed.function_call.arguments}"
            )

            # Add the assistant message with the approval request
            new_inputs.append(Message(role="assistant", contents=[user_input_needed]))

            # Get user approval
            user_approval = await asyncio.to_thread(input, "\nApprove function call? (y/n): ")

            # Add the user's approval response using Content.from_function_approval_response
            approval_response = Content.from_function_approval_response(
                approved=user_approval.lower() == "y",
                id=user_input_needed.id,
                function_call=user_input_needed.function_call,
            )
            new_inputs.append(
                Message(role="user", contents=[approval_response])
            )

        # Run again with all the context
        result = await agent.run(new_inputs)

    return result


async def handle_approvals_streaming(query: str, agent: "Agent") -> None:
    """Handle function call approvals with streaming responses.

    When we don't have a thread, we need to ensure we include the original query,
    the approval request, and the approval response in each iteration.
    """
    current_input: str | list[Any] = query
    has_user_input_requests = True
    while has_user_input_requests:
        has_user_input_requests = False
        user_input_requests: list[Any] = []

        # Stream the response
        async for chunk in agent.run(current_input, stream=True):
            if chunk.text:
                print(chunk.text, end="", flush=True)

            # Collect user input requests from the stream
            if chunk.user_input_requests:
                user_input_requests.extend(chunk.user_input_requests)

        if user_input_requests:
            has_user_input_requests = True
            # Start with the original query
            new_inputs: list[Any] = [query]

            for user_input_needed in user_input_requests:
                print(
                    f"\n\nUser Input Request for function from {agent.name}:"
                    f"\n  Function: {user_input_needed.function_call.name}"
                    f"\n  Arguments: {user_input_needed.function_call.arguments}"
                )

                # Add the assistant message with the approval request
                new_inputs.append(Message(role="assistant", contents=[user_input_needed]))

                # Get user approval
                user_approval = await asyncio.to_thread(input, "\nApprove function call? (y/n): ")

                # Add the user's approval response using Content.from_function_approval_response
                from agent_framework import Content
                approval_response = Content.from_function_approval_response(
                    approved=user_approval.lower() == "y",
                    id=user_input_needed.id,
                    function_call=user_input_needed.function_call,
                )
                new_inputs.append(
                    Message(role="user", contents=[approval_response])
                )

            # Update input with all the context for next iteration
            current_input = new_inputs


async def run_weather_agent_with_approval(is_streaming: bool) -> None:
    """Example showing AI function with approval requirement."""
    print(f"\n=== Weather Agent with Approval Required ({'Streaming' if is_streaming else 'Non-Streaming'}) ===\n")

    async with Agent(
        client=medium_client,
        name="WeatherAgent",
        instructions=("You are a helpful weather assistant. Use the get_weather tool to provide weather information."),
        tools=[get_weather, get_weather_detail],
    ) as agent:
        query = "Can you give me an update of the weather in LA and Portland and detailed weather for Seattle?"
        print(f"User: {query}")

        if is_streaming:
            print(f"\n{agent.name}: ", end="", flush=True)
            await handle_approvals_streaming(query, agent)
            print()
        else:
            result = await handle_approvals(query, agent)
            print(f"\n{agent.name}: {result}\n")


async def main() -> None:
    print("=== Demonstration of a tool with approvals ===\n")

    await run_weather_agent_with_approval(is_streaming=False)
    await run_weather_agent_with_approval(is_streaming=True)


if __name__ == "__main__":
    asyncio.run(main())