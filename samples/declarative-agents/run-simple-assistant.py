# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client
import os
import asyncio
from pathlib import Path
from random import randint
from typing import Literal

from agent_framework_declarative import AgentFactory

from dotenv import load_dotenv

load_dotenv()

def get_weather(location: str, unit: Literal["celsius", "fahrenheit"] = "celsius") -> str:
    """A simple function tool to get weather information."""
    return f"The weather in {location} is {randint(-10, 30) if unit == 'celsius' else randint(30, 100)} degrees {unit}."


async def main():
    """Create an agent from a declarative yaml specification and run it."""
    # get the path
    current_path = Path(__file__).parent
    yaml_path = current_path / "weather-assistant.yaml"

    # load the yaml from the path
    with yaml_path.open("r") as f:
        yaml_str = f.read()

    medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")

    medium_client=create_chat_client(medium_model_name)

    # create the AgentFactory with a chat client and bindings
    agent_factory = AgentFactory(
        chat_client=medium_client,
        bindings={"get_weather": get_weather},
    )
    # create the agent from the yaml
    agent = agent_factory.create_agent_from_yaml(yaml_str)
    # use the agent
    response = await agent.run("What's the weather in Amsterdam, in celsius?")
    print("Agent response:", response.text)


if __name__ == "__main__":
    asyncio.run(main())