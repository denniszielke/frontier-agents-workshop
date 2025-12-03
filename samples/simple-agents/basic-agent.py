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

from pydantic import Field

from dotenv import load_dotenv

load_dotenv()


"""
OpenAI Chat Client Direct Usage Example

Demonstrates direct OpenAIChatClient usage for chat interactions with OpenAI models.
Shows function calling capabilities with custom business logic.

"""

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client=create_chat_client(completion_model_name)

medium_client=create_chat_client(medium_model_name)

small_client=create_chat_client(small_model_name)


def get_weather_at_location(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the realtime weather for a given location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


async def main() -> None:
    client = small_client
    message = "What's the weather in Amsterdam and in Paris?"
    stream = False
    print(f"User: {message}")
    if stream:
        print("Assistant: ", end="")
        async for chunk in client.get_streaming_response(message, tools=get_weather_at_location):
            if chunk.text:
                print(chunk.text, end="")
        print("")
    else:
        response = await client.get_response(message, tools=get_weather_at_location)
        print(f"Assistant: {response}")


if __name__ == "__main__":
    asyncio.run(main())