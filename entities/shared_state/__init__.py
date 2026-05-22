# Copyright (c) Microsoft. All rights reserved.
"""Shared State Customer Support workflow for DevUI discovery.

Workflow: intent_extractor → bridge → response_generator → output
Demonstrates shared state passing between executor functions.
"""

import sys
from pathlib import Path

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel

from agent_framework import (
    Agent,
    AgentExecutorRequest,
    AgentExecutorResponse,
    ChatOptions,
    Message,
    Role,
    WorkflowBuilder,
    WorkflowContext,
    executor,
)
from samples.shared.model_client import create_chat_client

load_dotenv()

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client = create_chat_client(completion_model_name)
medium_client = create_chat_client(medium_model_name)
small_client = create_chat_client(small_model_name)


class IntentResult(BaseModel):
    intent: str
    confidence: float
    missing_info: list[str] = []


class ResponseResult(BaseModel):
    response: str
    next_action: str


INTENT_PROMPT = """You are a customer support intent classifier.
## extract these entities when present:

- **order_id**: Pattern ORD-XXXX (e.g., ORD-5678)
- **account_id**: Pattern ACC-XXXX (e.g., ACC-1234)
- **invoice_number**: Pattern INV-XXXX (e.g., INV-9876)
- **product_name**: The specific feature, software, or item having issues

Classify the message into ONE of these intents:
- **order_status**: Questions about orders, packages, delivery, shipping, tracking
- **billing**: Questions about bills, charges, invoices, payments, costs
- **refund**: Explicit refund requests, overcharge complaints, dispute charges
- **technical**: Problems with products, errors, bugs, things not working
- **account**: Requests to change/update account info, email, password, settings
- **unknown**: Random/off-topic messages

Rules:
- Use high confidence (>0.8) when keywords clearly match
- Use low confidence (<0.3) for off-topic/random messages
- List any missing info needed (order_id, account_id, product_name, etc.)

Return JSON with: intent, confidence (0-1), missing_info (list)."""

RESPONSE_PROMPT = """You are a helpful customer support agent.

Given the customer message and intent analysis:
- If confidence >= 0.8: Give a specific, helpful response about that topic
- If 0.3 <= confidence < 0.8: Ask a clarifying question
- If confidence < 0.3 or intent is "unknown": Ask a generic clarification question
- If missing_info is not empty: Ask for the specific missing information

Return JSON with: response (max 200 words), next_action (reply|ask_for_info)."""

intent_agent = Agent(
    completion_client,
    instructions=INTENT_PROMPT,
    name="intent_extractor",
    default_options=ChatOptions(response_format=IntentResult),
)

response_agent = Agent(
    medium_client,
    instructions=RESPONSE_PROMPT,
    name="response_generator",
    default_options=ChatOptions(response_format=ResponseResult),
)


@executor(id="start")
async def start(message: str, ctx: WorkflowContext) -> None:
    """Entry point - forward message to intent agent."""
    await ctx.set_shared_state("message", message)
    await ctx.send_message(AgentExecutorRequest(
        messages=[Message(role=Role.USER, contents=[message])],
        should_respond=True
    ))


@executor(id="bridge")
async def bridge(resp: AgentExecutorResponse, ctx: WorkflowContext) -> None:
    """Bridge intent result to response agent."""
    extraction = json.loads(resp.agent_response.text)
    message = await ctx.get_shared_state("message")

    context = f"""Message: {message}
Intent: {extraction['intent']} (confidence: {extraction['confidence']})
Missing Info: {', '.join(extraction.get('missing_info', [])) or 'none'}"""

    await ctx.send_message(AgentExecutorRequest(
        messages=[Message(role=Role.USER, contents=[context])],
        should_respond=True
    ))


@executor(id="output")
async def output(resp: AgentExecutorResponse, ctx: WorkflowContext) -> None:
    """Output final response."""
    result = json.loads(resp.agent_response.text)
    await ctx.yield_output(result['response'])


workflow = (
    WorkflowBuilder(start_executor=start)
    .add_edge(start, intent_agent)
    .add_edge(intent_agent, bridge)
    .add_edge(bridge, response_agent)
    .add_edge(response_agent, output)
    .build()
)
