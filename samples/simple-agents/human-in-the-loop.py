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
from agent_framework import ChatAgent, ChatMessage, Role
from agent_framework import ai_function
from pydantic import Field
import random

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

@ai_function(approval_mode="always_require")
def submit_payment(
    amount: Annotated[float, "Payment amount in USD"],
    recipient: Annotated[str, "Recipient name or vendor ID"],
    reference: Annotated[str, "Short description for the payment reference"],
) -> str:
    """
    Submit a payment request to the external payments system.

    This operation has financial impact and should always be reviewed
    and approved by a human before it is executed.
    """
    # In a real scenario this would call an external payments API.
    # Here we just simulate the side effect.
    return (
        f"Payment of ${amount:.2f} to '{recipient}' has been submitted "
        f"with reference '{reference}'."
    )

@ai_function(
    name="get_account_balance",
    description="Retrieves the current account balance for the user in USD"
)
def get_account_balance() -> float:
    """
    Get the current account balance for the user.
    
    Returns:
        float: The account balance in USD (numeric value only, no formatting).
    
    This operation is read-only and does not require approval.
    """
    # Generate a random balance between 1000 and 5000 USD
    balance = random.uniform(1000, 5000)
    return round(balance, 2)


# Stateful agent wired to Azure OpenAI plus both banking tools
agent = ChatAgent(
    chat_client=medium_client,
    name="FinanceAgent",
    instructions=(
        "You are an agent from Contoso Bank. You assist users with financial operations "
        "and provide clear explanations. For transfers only amount, recipient name, and reference are needed."
    ),
    tools=[submit_payment, get_account_balance],
)

async def main():
    # Preserve conversation memory across the entire console session
    thread = agent.get_new_thread()
    print("=== FinanceAgent - Interactive Session ===")
    print("Type 'exit' or 'quit' to end the conversation\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        if not user_input:
            continue

        print("\nAgent: ", end="", flush=True)
        result = await agent.run(user_input, thread=thread)

        if result.user_input_requests:
            print("\n\n=== APPROVALS REQUIRED ===")
            approval_messages: list[ChatMessage] = []
            # Surface every pending tool call and gather a decision per call
            for req in result.user_input_requests:
                print(f"- Function: {req.function_call.name}")
                print(f"  Arguments: {req.function_call.arguments}")
                approved = input(f"Approve '{req.function_call.name}'? (yes/no): ").strip().lower() == "yes"
                # Encode the approval/denial into a ChatMessage the framework consumes
                approval_messages.append(
                    ChatMessage(role=Role.USER, contents=[req.create_response(approved)])
                )

            # Resume the prior run once all approvals are ready
            followup = await agent.run(approval_messages, thread=thread, prior_run=result)
            print("\nAgent:", followup.text)
        else:
            print(result.text)

        print()


if __name__ == "__main__":
    asyncio.run(main())