# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client

"""Magentic Workflow Example.

This module demonstrates a multi-agent workflow using the Magentic framework.
It orchestrates two specialized agents (Researcher and Coder) to collaboratively
solve complex tasks that require both information gathering and computational analysis.

The example workflow:
1. A ResearcherAgent gathers information from various sources
2. A CoderAgent performs data processing and quantitative analysis
3. A standard manager orchestrates the collaboration between agents
4. Events are streamed in real-time to provide visibility into the workflow

Requirements:
- Azure OpenAI service configured with appropriate credentials
- Environment variables loaded from .env file
- Azure CLI authentication configured
"""
import os
import asyncio
import logging
from datetime import datetime

import pytz
from dotenv import load_dotenv
from agent_framework import (
    ChatAgent,
    MagenticAgentDeltaEvent,
    MagenticAgentMessageEvent,
    MagenticBuilder,
    MagenticFinalResultEvent,
    MagenticOrchestratorMessageEvent,
    WorkflowEvent,
)

# Configure logging to debug level for detailed workflow tracking
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file (e.g., Azure credentials, endpoints)
load_dotenv()

logger.info("Environment variables loaded successfully")

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client=create_chat_client(completion_model_name)
medium_client=create_chat_client(medium_model_name)
small_client=create_chat_client(small_model_name)

async def get_weather(city: str) -> str:
    """Gets a statement about the current weather in the given city."""
    print("executing get_weather")
    return f"The weather in {city} is 73 degrees and Sunny."


async def get_medical_history(username: str) -> str:
    """Get the medical history for a given username with allergies and restrictions."""
    print("executing get_medical_history")
    return f"{username} has an allergy to peanuts and eggs."


async def get_available_ingredients(location: str) -> str:
    """Get the available ingredients and their prices for a given location.

    The response MUST clearly list each ingredient with a price in euros,
    for example: "eggs (2.50€)", "milk (1.80€)", etc., so other agents
    can reason about cost.
    """
    print("executing get_available_ingredients")
    return (
        f"Available ingredients in {location} with typical prices are: "
        f"eggs (2.50€), milk (1.80€), bread (3.00€), peanuts (4.00€), beer (2.00€), "
        f"wine (8.00€), salmon (12.00€), spinach (2.20€), oil (3.50€) and butter (2.70€)."
    )


def get_current_username() -> str:
    """Get the username of the current user."""
    print("executing get_current_username")
    return "Dennis"


def get_current_location_of_user(username: str) -> str:
    """Get the current timezone location of the user for a given username."""
    print("executing get_current_location")
    print(username)
    if "Dennis" in username:
        return "Europe/Berlin"
    return "America/New_York"


def get_current_time(location: str) -> str:
    """Get the current time in the given location using pytz."""
    try:
        print("get current time for location:", location)
        timezone = pytz.timezone(location)
        now = datetime.now(timezone)
        current_time = now.strftime("%I:%M:%S %p")
        return current_time
    except Exception as exc:  # pragma: no cover - defensive
        print("Error:", exc)
        return "Sorry, I couldn't find the timezone for that location."


def get_budget_limit(username: str) -> str:
    """Return a random food budget limit in euros between 20 and 50.

    Other agents should treat this value as a hard upper limit when
    proposing meals or shopping lists.
    """
    import random

    print("executing get_budget_limit")
    limit = random.randint(20, 50)
    return f"The user's total food budget is {limit}€ (hard limit)."


def get_user_preferences(username: str) -> str:
    """Return randomized user food preferences and constraints.

    The response MUST always specify all of the following explicitly so
    other agents can reason about them:

    - Whether the user wants to eat now or later
    - Whether the user prefers delivery to a concrete address or dining in
    - Whether spending must stay within the budget or can exceed it
    """
    import random

    print("executing get_user_preferences")

    eat_timing = random.choice(["eat now", "eat later"])
    location_mode = random.choice([
        "delivery to the home address",
        "delivery to the office address",
        "dine in at a nearby restaurant",
    ])
    budget_policy = random.choice([
        "must strictly stay within the budget limit",
        "can exceed the budget limit if the meal is exceptional",
    ])

    return (
        f"For user {username}, preferences are: wants to {eat_timing}, "
        f"prefers {location_mode}, and {budget_policy}."
    )


async def run_magentic_workflow() -> None:
    """Run a Magentic multi-agent workflow mirroring the Autogen example.

    Agents:
        - users_agent: knows username and medical history
        - location_agent: knows the user's physical location
        - time_agent: knows local time for a location
        - chef_agent: recommends meals based on time, location, ingredients
    """

    users_agent = ChatAgent(
        name="users_agent",
        description=(
            "Assistant focused on user-specific information: identity, "
            "medical history, allergies, food budget constraints and "
            "general dining preferences."
        ),
        instructions=(
            "You are responsible ONLY for user-specific context. "
            "Use your tools to find the current username, the user's "
            "medical history (including allergies and restrictions), a "
            "random but realistic budget limit between 20€ and 50€, and "
            "clear dining preferences (eat now or later, delivery address "
            "vs. dine in, and whether the user must stay within budget or "
            "is allowed to go above it). "
            "Do not make meal recommendations or reason about ingredients "
            "directly; instead, provide clear, concise facts that other "
            "agents can rely on. Always explicitly mention allergens, the "
            "exact budget number in euros, and all dining preferences when "
            "asked about them."
        ),
        chat_client=small_client,
        tools=[
            get_current_username,
            get_medical_history,
            get_budget_limit,
            get_user_preferences,
        ],
    )

    manager_agent = ChatAgent(
        name="manager_agent",
        description=(
            "Assistant that manages contextual information about the user's "
            "location and current local time."
        ),
        instructions=(
            "You are responsible ONLY for resolving the user's physical "
            "location and the current local time at that location. "
            "Use your tools to first determine the location from the "
            "username when necessary, and then compute an accurate current "
            "time string for that location. Do NOT suggest meals, reason "
            "about ingredients, or discuss allergies or budget. Instead, "
            "return short factual statements like 'The user is in X' or "
            "'The local time in X is Y'."
        ),
        chat_client=medium_client,
        tools=[get_current_location_of_user, get_current_time],
    )

    chef_agent = ChatAgent(
        name="chef_agent",
        description=(
            "A helpful assistant that can suggest meals and dishes for the right "
            "time of the day, location, available ingredients, user preferences "
            "and allergies."
        ),
        instructions=(
            "Recommend dishes for the right time of the day, location, available "
            "ingredients and user preferences. Always ask for food preferences "
            "and allergies. Never suggest a dish until allergies are clarified." 
        ),
        chat_client=small_client,
        tools=[get_available_ingredients, get_weather],
    )
    
    # State variables for managing streaming display output
    # These track which agent is currently streaming and whether a line is open
    last_stream_agent_id: str | None = None  # ID of the agent that last sent a delta
    stream_line_open: bool = False  # Whether we're currently in the middle of streaming

    # Unified callback for all workflow events
    def on_event(event: WorkflowEvent) -> None:
        """Process and display events emitted by the Magentic workflow."""
        nonlocal last_stream_agent_id, stream_line_open
        
        # Handle orchestrator messages (workflow coordination events)
        if isinstance(event, MagenticOrchestratorMessageEvent):
            print(f"\n[ORCH:{event.kind}]\n\n{getattr(event.message, 'text', '')}\n{'-' * 26}")
            
        # Handle streaming delta events (token-by-token agent responses)
        elif isinstance(event, MagenticAgentDeltaEvent):
            # Ignore empty or non-text deltas to avoid printing "None"
            if not isinstance(event.text, str) or not event.text:
                return

            # Start a new stream line if agent changed or no stream is currently open
            if last_stream_agent_id != event.agent_id or not stream_line_open:
                if stream_line_open:
                    print()  # Close previous stream line
                print(f"\n[STREAM:{event.agent_id}]: ", end="", flush=True)
                last_stream_agent_id = event.agent_id
                stream_line_open = True
            # Print the delta text without newline for continuous streaming
            print(event.text, end="", flush=True)
            
        # Handle complete agent message events
        elif isinstance(event, MagenticAgentMessageEvent):
            # Close any open stream line before showing final message
            if stream_line_open:
                print(" (final)")  # Mark end of streaming
                stream_line_open = False
                print()
            # Display the complete agent message
            msg = event.message
            if msg is not None:
                # Flatten newlines for compact display
                response_text = (msg.text or "").replace("\n", " ")
                print(f"\n[AGENT:{event.agent_id}] {msg.role.value}\n\n{response_text}\n{'-' * 26}")
                
        # Handle final result event (workflow completion)
        elif isinstance(event, MagenticFinalResultEvent):
            print("\n" + "=" * 50)
            print("FINAL RESULT:")
            print("=" * 50)
            if event.message is not None:
                print(event.message.text)
            print("=" * 50)


    print("\n---------------------------------------------------------------------")
    print("\nBuilding Magentic Workflow...")
    print("\n---------------------------------------------------------------------")

    # Build the Magentic workflow using the builder pattern
    workflow = (
        MagenticBuilder()
        .participants(
            users=users_agent,
            manager=manager_agent,
            chef=chef_agent,
        )
        .with_standard_manager(
            chat_client=completion_client,
            max_round_count=20,
            max_stall_count=4,
            max_reset_count=1,
        )
        .build()
    )

    task = "I want to have something to eat. What would you recommend for me for now?"

    print(f"\nTask: {task}")
    print("\nStarting workflow execution...")
    
    try:
        # Execute the workflow with streaming enabled
        # This returns an async generator yielding events as they occur
        async for event in workflow.run_stream(task):
            # Process each event
            on_event(event)

        print(f"Workflow completed!")
    except Exception as e:
        # Handle any errors during workflow execution
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        print(f"Workflow execution failed: {e}")

async def main() -> None:
    """Entry point for the Magentic workflow application.
    
    This function serves as the main entry point and orchestrates
    the execution of the Magentic multi-agent workflow.
    """
    await run_magentic_workflow()


# Script entry point
# When run as a script (not imported), execute the main async function
if __name__ == "__main__":
    asyncio.run(main())