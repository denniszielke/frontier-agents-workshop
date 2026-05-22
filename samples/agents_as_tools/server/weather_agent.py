# Copyright (c) Microsoft. All rights reserved.

import os
import asyncio
import logging
from collections.abc import AsyncIterable
from random import randint
from typing import Any, Annotated

from agent_framework import (
    AgentResponse,
    AgentResponseUpdate,
    AgentSession,
    BaseAgent,
    Message,
    Content,
    Role,
)
from agent_framework.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import Field

"""Weather Agent Implementation Example

This sample demonstrates implementing a custom agent by extending BaseAgent,
while delegating weather-related questions to an OpenAI model that can call a
`get_weather` tool.
"""


load_dotenv()

logger = logging.getLogger("weather_agent")

if (os.environ.get("GITHUB_TOKEN") is not None):
    token = os.environ["GITHUB_TOKEN"]
    endpoint = "https://models.github.ai/inference"
    print("Using GitHub Token for authentication")
elif (os.environ.get("AZURE_OPENAI_API_KEY") is not None):
    token = os.environ["AZURE_OPENAI_API_KEY"]
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
    print("Using Azure OpenAI Token for authentication")

async_openai_client = AsyncOpenAI(
    base_url=endpoint,
    api_key=token
)

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client=OpenAIChatCompletionClient(
    model = completion_model_name,
    api_key=token,
    async_client = async_openai_client
)

medium_client=OpenAIChatCompletionClient(
    model = medium_model_name,
    api_key=token,
    async_client = async_openai_client
)

small_client=OpenAIChatCompletionClient(
    model = small_model_name,
    api_key=token,
    async_client = async_openai_client
)


def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location.

    This is a simple mock implementation used as a tool function
    for the language model.
    """

    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    condition = conditions[randint(0, 3)]
    temperature = randint(10, 30)
    forecast = f"The weather in {location} is {condition} with a high of {temperature}°C."

    logger.info(
        "Generated mock weather forecast",
        extra={"location": location, "condition": condition, "temperature": temperature},
    )

    return forecast


class WeatherAgent(BaseAgent):
    """A custom agent that can answer weather questions via a tool.

    The agent keeps the same structure as the echo example but delegates
    response generation to an OpenAI model using the `get_weather` tool.
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the WeatherAgent.

        Args:
            name: The name of the agent.
            description: The description of the agent.
            **kwargs: Additional keyword arguments passed to BaseAgent.
        """
        super().__init__(
            name=name,
            description=description,
            **kwargs,
        )

    async def run(
        self,
        messages: str | Message | list[str] | list[Message] | None = None,
        *,
        stream: bool = False,
        session: AgentSession | None = None,
        **kwargs: Any,
    ) -> AgentResponse:
        logger.info("WeatherAgent.run called", extra={"agent_id": self.id})

        normalized_messages = self._normalize_messages(messages)

        if not normalized_messages:
            user_text = "Hello! You can ask me about the weather in different cities."
        else:
            last_message = normalized_messages[-1]
            user_text = last_message.text or "Tell me about the weather."

        logger.info("WeatherAgent handling query", extra={"agent_id": self.id, "user_text": user_text})

        # Delegate reply generation to the OpenAI client using the weather tool
        response = await small_client.get_response(user_text, tools=get_weather)
        reply_text = str(response)

        logger.info(
            "WeatherAgent model response ready",
            extra={"agent_id": self.id, "response_preview": reply_text[:200]},
        )

        response_message = Message(
            role=Role.ASSISTANT,
            contents=[Content('text', text=reply_text)],
        )

        return AgentResponse(messages=[response_message])

    async def run_stream(
        self,
        messages: str | Message | list[str] | list[Message] | None = None,
        *,
        session: AgentSession | None = None,
        **kwargs: Any,
    ) -> AsyncIterable[AgentResponseUpdate]:
        logger.info("WeatherAgent.run_stream called", extra={"agent_id": self.id})

        normalized_messages = self._normalize_messages(messages)

        if not normalized_messages:
            user_text = "Hello! You can ask me about the weather in different cities."
        else:
            last_message = normalized_messages[-1]
            user_text = last_message.text or "Tell me about the weather."

        full_text_chunks: list[str] = []

        async for chunk in small_client.get_streaming_response(user_text, tools=get_weather):
            if chunk.text:
                full_text_chunks.append(chunk.text)
                logger.debug(
                    "WeatherAgent streaming chunk",
                    extra={"agent_id": self.id, "chunk_length": len(chunk.text)},
                )
                yield AgentResponseUpdate(
                    contents=[Content('text', text=chunk.text)],
                    role=Role.ASSISTANT,
                )

        # Log streaming completion
        if full_text_chunks:
            logger.info(
                "WeatherAgent streaming complete",
                extra={"agent_id": self.id, "total_length": len("".join(full_text_chunks))},
            )


async def main() -> None:
    """Demonstrates how to use the custom WeatherAgent."""
    print("=== Weather Agent Example ===\n")

    # Create WeatherAgent
    print("--- WeatherAgent Example ---")
    weather_agent = WeatherAgent(
        name="WeatherBot", description="An agent that can answer weather questions using a tool"
    )

    # Test non-streaming
    print(f"Agent Name: {weather_agent.name}")
    print(f"Agent ID: {weather_agent.id}")

    query = "What's the weather in Amsterdam and in Paris?"
    print(f"\nUser: {query}")
    result = await weather_agent.run(query)
    print(f"Agent: {result.text}")

    # Test streaming
    query2 = "And what about Berlin tomorrow?"
    print(f"\nUser: {query2}")
    print("Agent: ", end="", flush=True)
    async for chunk in weather_agent.run_stream(query2):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()

    # Example with sessions
    print("\n--- Using WeatherAgent with Session ---")
    session = weather_agent.create_session()

    # First message
    result1 = await weather_agent.run("What's the weather in Seattle?", session=session)
    print("User: What's the weather in Seattle?")
    print(f"Agent: {result1.text}")

    # Second message in same session
    result2 = await weather_agent.run("And how about Tokyo?", session=session)
    print("User: And how about Tokyo?")
    print(f"Agent: {result2.text}")


if __name__ == "__main__":
    asyncio.run(main())