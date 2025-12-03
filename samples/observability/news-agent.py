# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client
import os
import asyncio
from typing import Annotated, List, Literal

import httpx
from agent_framework import ChatAgent
from agent_framework.observability import get_tracer, setup_observability
from agent_framework.openai import OpenAIChatClient
from opentelemetry.trace import SpanKind
from pydantic import Field

from openai import AsyncOpenAI

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


def get_hackernews_story_ids(
    list_type: Annotated[
        Literal["top", "new", "best"],
        Field(description="Which Hacker News list to fetch: 'top', 'new', or 'best'."),
    ] = "top",
    limit: Annotated[
        int,
        Field(
            description="Maximum number of story IDs to return (1-50).",
            ge=1,
            le=50,
        ),
    ] = 10,
) -> List[int]:
    """Get a list of recent Hacker News story IDs using the Firebase API."""
    base = "https://hacker-news.firebaseio.com/v0"
    path_map = {
        "top": "topstories",
        "new": "newstories",
        "best": "beststories",
    }
    path = path_map[list_type]
    url = f"{base}/{path}.json"

    with httpx.Client(timeout=10) as client:
        response = client.get(url, params={"print": "pretty"})
        response.raise_for_status()
        ids = response.json() or []

    return ids[:limit]


def get_hackernews_story(
    story_id: Annotated[
        int,
        Field(description="The Hacker News story ID to retrieve."),
    ],
) -> dict:
    """Get the full JSON details of a Hacker News story by ID."""
    base = "https://hacker-news.firebaseio.com/v0"
    url = f"{base}/item/{story_id}.json"

    with httpx.Client(timeout=10) as client:
        response = client.get(url, params={"print": "pretty"})
        response.raise_for_status()
        data = response.json() or {}

    return data


async def main() -> None:
    print("=== Hacker News Agent (with observability) ===\n")

    # Enable tracing / metrics based on environment configuration
    setup_observability()

    tracer = get_tracer()

    async def get_hn_ids_observed(*args, **kwargs):
        with tracer.start_as_current_span(
            "tool:get_hackernews_story_ids", kind=SpanKind.CLIENT
        ) as span:
            span.set_attribute("tool.name", "get_hackernews_story_ids")
            return get_hackernews_story_ids(*args, **kwargs)

    async def get_hn_story_observed(*args, **kwargs):
        with tracer.start_as_current_span(
            "tool:get_hackernews_story", kind=SpanKind.CLIENT
        ) as span:
            span.set_attribute("tool.name", "get_hackernews_story")
            return get_hackernews_story(*args, **kwargs)

    agent = ChatAgent(
        chat_client=medium_client,
        instructions=(
            "You are a helpful news assistant that uses the provided tools "
            "to fetch and summarize Hacker News stories. When asked about "
            "Hacker News, first fetch relevant story IDs, then retrieve "
            "their details and provide concise summaries."
        ),
        tools=[get_hn_ids_observed, get_hn_story_observed],
    )

    thread = agent.get_new_thread()

    user_queries = [
        "Give me a brief summary of the current top 5 Hacker News stories.",
        "Now, focus on any stories related to AI or machine learning.",
        "Remind me which story had the highest score.",
    ]

    for query in user_queries:
        print(f"User: {query}")
        result = await agent.run(query, thread=thread)
        print(f"Agent: {result.text}\n")


if __name__ == "__main__":
    asyncio.run(main())