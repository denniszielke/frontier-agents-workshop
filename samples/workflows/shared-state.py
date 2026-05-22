# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client

"""
Minimal Customer Support Workflow

A simplified two-agent workflow demonstrating the Agent Framework.
Uses agents directly as executors with inline prompts.

Workflow: intent_extractor → response_generator

Use case: Customer support message handling.
Given a customer message, the workflow:
1. Extracts the intent and confidence using the intent_extractor agent.
2. Generates an appropriate response using the response_generator agent based on the extracted intent.  
The workflow outputs the final response to the user.
# Example 1: Order status inquiry
python samples/workflows/shared-state.py "where is my package ORD-123"

# Example 2: Billing question
python samples/workflows/shared-state.py "I was charged twice on invoice INV-5678"
"""

import asyncio
import json
import os
import sys
from agent_framework import (
    executor,
    WorkflowBuilder,
    WorkflowContext,
    AgentExecutorRequest,
    AgentExecutorResponse,
    Message,
    ChatOptions,
)
from dotenv import load_dotenv
from pydantic import BaseModel
from agent_framework import Agent

# ============================================================================
# Pydantic Models
# ============================================================================

class IntentResult(BaseModel):
    intent: str  # billing|refund|order_status|technical|account|unknown
    confidence: float
    missing_info: list[str] = []


class ResponseResult(BaseModel):
    response: str
    next_action: str  # reply|ask_for_info


# ============================================================================
# Inline Prompts
# ============================================================================

INTENT_PROMPT = """You are a customer support intent classifier.
## extract these entities when present:

- **order_id**: Pattern ORD-XXXX (e.g., ORD-5678)
- **account_id**: Pattern ACC-XXXX (e.g., ACC-1234)
- **invoice_number**: Pattern INV-XXXX (e.g., INV-9876)
- **product_name**: The specific feature, software, or item having issues (e.g., "Mobile App", "Login Page")


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
- "help with order" = order_status, NOT refund
- List any missing info needed (order_id, account_id, product_name, etc.)

Return JSON with: intent, confidence (0-1), missing_info (list)."""

RESPONSE_PROMPT = """You are a helpful customer support agent.

Given the customer message and intent analysis:
- If confidence >= 0.8: Give a specific, helpful response about that topic, reference any need for missing info
- If 0.3 <= confidence < 0.8: Ask a clarifying question to better understand the customer's needs. reference you need missing data if any
- If confidence < 0.3 or intent is "unknown": Ask a generic clarification question
- If missing_info is not empty: Ask for the specific missing information

Return JSON with: response (max 200 words), next_action (reply|ask_for_info)."""


# ============================================================================
# Azure OpenAI Setup
# ============================================================================

load_dotenv()
completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client=create_chat_client(completion_model_name)
medium_client=create_chat_client(medium_model_name)
small_client=create_chat_client(small_model_name)    

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


# ============================================================================
# Executors
# ============================================================================

@executor(id="start")
async def start(message: str, ctx: WorkflowContext) -> None:
    """Entry point - forward message to intent agent."""
    print(f"\n Step 1: Storing message")
    ctx.set_state("message", message)
    print(f"→ Forwarding to intent_agent")
    await ctx.send_message(AgentExecutorRequest(
        messages=[Message(role="user", contents=[message])],
        should_respond=True
    ))


@executor(id="bridge")
async def bridge(resp: AgentExecutorResponse, ctx: WorkflowContext) -> None:
    """Bridge intent result to response agent."""
    extraction = json.loads(resp.agent_response.text)
    message = ctx.get_state("message")
    
    print(f"\n Step 2: Intent extracted")
    print(f"   Intent: {extraction['intent']}")
    print(f"   Confidence: {extraction['confidence']:.2f}")
    print(f"   Missing: {', '.join(extraction.get('missing_info', [])) or 'none'}")
    
    context = f"""Message: {message}
Intent: {extraction['intent']} (confidence: {extraction['confidence']})
Missing Info: {', '.join(extraction.get('missing_info', [])) or 'none'}"""
    
    print(f"→ Forwarding to response_agent")
    await ctx.send_message(AgentExecutorRequest(
        messages=[Message(role="user", contents=[context])],
        should_respond=True
    ))


@executor(id="output")
async def output(resp: AgentExecutorResponse, ctx: WorkflowContext) -> None:
    """Output final response."""
    result = json.loads(resp.agent_response.text)
    print(f"\n Step 3: Response generated")
    print(f"\n{'='*60}")
    print(f"Response: {result['response']}")
    print(f"Action: {result['next_action']}")
    print(f"{'='*60}\n")
    await ctx.yield_output(result['response'])


# ============================================================================
# Workflow
# ============================================================================

workflow = (
    WorkflowBuilder(start_executor=start)
    .add_edge(start, intent_agent)
    .add_edge(intent_agent, bridge)
    .add_edge(bridge, response_agent)
    .add_edge(response_agent, output)
    .build()
)


def main():
    """Launch the shared-state workflow in DevUI."""
    import logging

    from agent_framework.devui import serve

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting Agent Workflow (Customer Support with Shared State)")
    logger.info("Available at: http://localhost:8093")
    logger.info("\nThis workflow demonstrates:")
    logger.info("- Shared state passing between executor functions")
    logger.info("- Workflow: intent_extractor → bridge → response_generator → output")

    serve(entities=[workflow], port=8093, auto_open=True, auth_enabled=False)


if __name__ == "__main__":
    main()