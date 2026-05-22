# Copyright (c) Microsoft. All rights reserved.
"""Content Review with Quality Routing workflow for DevUI discovery.

Writer → Reviewer → [branches]:
  - score >= 80: → Publisher → Summarizer
  - score < 80: → Editor → Publisher → Summarizer
"""

import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
from typing import Any

from dotenv import load_dotenv
from pydantic import BaseModel

from agent_framework import Agent, AgentExecutorResponse, WorkflowBuilder, ChatOptions
from samples.shared.model_client import create_chat_client

load_dotenv()

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client = create_chat_client(completion_model_name)
medium_client = create_chat_client(medium_model_name)
small_client = create_chat_client(small_model_name)


class ReviewResult(BaseModel):
    """Review evaluation with scores and feedback."""
    score: int
    feedback: str
    clarity: int
    completeness: int
    accuracy: int
    structure: int


def needs_editing(message: Any) -> bool:
    """Check if content needs editing based on review score."""
    if not isinstance(message, AgentExecutorResponse):
        return False
    try:
        review = ReviewResult.model_validate_json(message.agent_response.text)
        return review.score < 80
    except Exception:
        return False


def is_approved(message: Any) -> bool:
    """Check if content is approved (high quality)."""
    if not isinstance(message, AgentExecutorResponse):
        return True
    try:
        review = ReviewResult.model_validate_json(message.agent_response.text)
        return review.score >= 80
    except Exception:
        return True


writer = Agent(
    small_client,
    name="Writer",
    instructions=(
        "You are an excellent content writer. "
        "Create clear, engaging content based on the user's request. "
        "Focus on clarity, accuracy, and proper structure."
    ),
)

reviewer = Agent(
    medium_client,
    name="Reviewer",
    instructions=(
        "You are an expert content reviewer. "
        "Evaluate the writer's content based on:\n"
        "1. Clarity - Is it easy to understand?\n"
        "2. Completeness - Does it fully address the topic?\n"
        "3. Accuracy - Is the information correct?\n"
        "4. Structure - Is it well-organized?\n\n"
        "Return a JSON object with:\n"
        "- score: overall quality (0-100)\n"
        "- feedback: concise, actionable feedback\n"
        "- clarity, completeness, accuracy, structure: individual scores (0-100)"
    ),
    default_options=ChatOptions(response_format=ReviewResult),
)

editor = Agent(
    completion_client,
    name="Editor",
    instructions=(
        "You are a skilled editor. "
        "You will receive content along with review feedback. "
        "Improve the content by addressing all the issues mentioned in the feedback. "
        "Maintain the original intent while enhancing clarity, completeness, accuracy, and structure."
    ),
)

publisher = Agent(
    small_client,
    name="Publisher",
    instructions=(
        "You are a publishing agent. "
        "You receive either approved content or edited content. "
        "Format it for publication with proper headings and structure."
    ),
)

summarizer = Agent(
    small_client,
    name="Summarizer",
    instructions=(
        "You are a summarizer agent. "
        "Create a final publication report that includes:\n"
        "1. A brief summary of the published content\n"
        "2. The workflow path taken (direct approval or edited)\n"
        "3. Key highlights and takeaways\n"
        "Keep it concise and professional."
    ),
)

workflow = (
    WorkflowBuilder(start_executor=writer)
    .add_edge(writer, reviewer)
    .add_edge(reviewer, publisher, condition=is_approved)
    .add_edge(reviewer, editor, condition=needs_editing)
    .add_edge(editor, publisher)
    .add_edge(publisher, summarizer)
    .build()
)
