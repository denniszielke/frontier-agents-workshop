import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client
"""Agent Workflow - Content Review with Quality Routing.

This sample demonstrates:
- Using agents directly as executors
- Conditional routing based on structured outputs
- Quality-based workflow paths with convergence

Use case: Content creation with automated review.
Writer creates content, Reviewer evaluates quality:
  - High quality (score >= 80): → Publisher → Summarizer
  - Low quality (score < 80): → Editor → Publisher → Summarizer
Both paths converge at Summarizer for final report.
"""

import os
from typing import Any

from agent_framework import ChatMessage, ConcurrentBuilder
from pydantic import Field
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client=create_chat_client(completion_model_name)
medium_client=create_chat_client(medium_model_name)
small_client=create_chat_client(small_model_name)    


researcher = completion_client.create_agent(
    instructions=(
        "You're an expert market and product researcher. Given a prompt, provide concise, factual insights,"
        " opportunities, and risks."
    ),
    name="researcher",
)

marketer = small_client.create_agent(
    instructions=(
        "You're a creative marketing strategist. Craft compelling value propositions and target messaging"
        " aligned to the prompt."
    ),
    name="marketer",
)

legal = medium_client.create_agent(
    instructions=(
        "You're a cautious legal/compliance reviewer. Highlight constraints, disclaimers, and policy concerns"
        " based on the prompt."
    ),
    name="legal",
)

workflow = ConcurrentBuilder().participants([researcher, marketer, legal]).build()

def main():
    """Launch the branching workflow in DevUI."""
    import logging

    from agent_framework.devui import serve

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting Agent Workflow (Content Review with Quality Routing)")
    logger.info("Available at: http://localhost:8093")
    logger.info("\nThis workflow demonstrates:")
    logger.info("- Conditional routing based on structured outputs")
    logger.info("- Path 1 (score >= 80): Reviewer → Publisher → Summarizer")
    logger.info("- Path 2 (score < 80): Reviewer → Editor → Publisher → Summarizer")
    logger.info("- Both paths converge at Summarizer for final report")

    serve(entities=[workflow], port=8093, auto_open=True)


if __name__ == "__main__":
    main()