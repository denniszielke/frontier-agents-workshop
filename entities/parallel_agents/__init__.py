# Copyright (c) Microsoft. All rights reserved.
"""Parallel Agents workflow for DevUI discovery.

Runs researcher, marketer, and legal agents concurrently on the same prompt.
"""

import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os

from dotenv import load_dotenv

from agent_framework import Agent
from agent_framework.orchestrations import ConcurrentBuilder
from samples.shared.model_client import create_chat_client

load_dotenv()

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client = create_chat_client(completion_model_name)
medium_client = create_chat_client(medium_model_name)
small_client = create_chat_client(small_model_name)

researcher = Agent(
    medium_client,
    instructions=(
        "You're an expert market and product researcher. Given a prompt, provide concise, factual insights,"
        " opportunities, and risks."
    ),
    name="researcher",
)

marketer = Agent(
    small_client,
    instructions=(
        "You're a creative marketing strategist. Craft compelling value propositions and target messaging"
        " aligned to the prompt."
    ),
    name="marketer",
)

legal = Agent(
    medium_client,
    instructions=(
        "You're a cautious legal/compliance reviewer. Highlight constraints, disclaimers, and policy concerns"
        " based on the prompt."
    ),
    name="legal",
)

workflow = ConcurrentBuilder(participants=[researcher, marketer, legal]).build()
