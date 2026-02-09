# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client

"""Handoff Workflow Example.

This module demonstrates a multi-agent workflow using the Handoff orchestration pattern.
It models a customer support triage scenario where agents explicitly hand off control
to specialized agents based on the customer's request.

The example workflow:
1. A triage_agent acts as coordinator, collecting basic information
2. Based on the issue type, it hands off to one of:
   - billing_agent for payment/invoice issues
   - shipping_agent for delivery/tracking issues
3. After specialist handles the issue, optionally hands off to compliance_agent
4. The handoff pattern preserves full conversation context throughout

Key differences from Magentic:
- Explicit handoffs (not automatic orchestration)
- Agents determine when to transfer control
- No central manager deciding next steps
- More like real-world escalation workflows

Requirements:
- Azure OpenAI service configured with appropriate credentials
- Environment variables loaded from .env file
- Azure CLI authentication configured
"""
import os
import asyncio
import logging

from dotenv import load_dotenv
from agent_framework import (
    ChatAgent,
    HandoffBuilder,
)

# Configure logging to debug level for detailed workflow tracking
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file (e.g., Azure credentials, endpoints)
load_dotenv()

logger.info("Environment variables loaded successfully")

completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

completion_client = create_chat_client(completion_model_name)
medium_client = create_chat_client(medium_model_name)
small_client = create_chat_client(small_model_name)


# Simulated data stores and tools
ORDERS_DB = {
    "ORD-12345": {
        "order_id": "ORD-12345",
        "customer": "Alice Johnson",
        "status": "shipped",
        "tracking_number": "TRACK-987654",
        "items": ["Widget A", "Gadget B"],
        "total": 129.99,
        "shipping_address": "123 Main St, Seattle, WA 98101"
    },
    "ORD-67890": {
        "order_id": "ORD-67890",
        "customer": "Bob Smith",
        "status": "processing",
        "tracking_number": None,
        "items": ["Device X"],
        "total": 299.99,
        "shipping_address": "456 Oak Ave, Portland, OR 97201"
    }
}

INVOICES_DB = {
    "INV-001": {
        "invoice_id": "INV-001",
        "order_id": "ORD-12345",
        "amount": 129.99,
        "status": "paid",
        "payment_method": "credit_card",
        "date": "2025-01-15"
    },
    "INV-002": {
        "invoice_id": "INV-002",
        "order_id": "ORD-67890",
        "amount": 299.99,
        "status": "pending",
        "payment_method": "paypal",
        "date": "2025-02-01"
    }
}


async def lookup_order(order_id: str) -> str:
    """Look up order details by order ID.
    
    Args:
        order_id: The order identifier (e.g., 'ORD-12345')
        
    Returns:
        Formatted order information or error message
    """
    print(f"[TOOL] lookup_order called with order_id={order_id}")
    order = ORDERS_DB.get(order_id)
    if not order:
        return f"Order {order_id} not found in system."
    
    return (
        f"Order {order['order_id']}:\n"
        f"  Customer: {order['customer']}\n"
        f"  Status: {order['status']}\n"
        f"  Items: {', '.join(order['items'])}\n"
        f"  Total: ${order['total']}\n"
        f"  Shipping Address: {order['shipping_address']}\n"
        f"  Tracking: {order['tracking_number'] or 'Not yet assigned'}"
    )


async def lookup_invoice(invoice_id: str) -> str:
    """Look up invoice details by invoice ID.
    
    Args:
        invoice_id: The invoice identifier (e.g., 'INV-001')
        
    Returns:
        Formatted invoice information or error message
    """
    print(f"[TOOL] lookup_invoice called with invoice_id={invoice_id}")
    invoice = INVOICES_DB.get(invoice_id)
    if not invoice:
        return f"Invoice {invoice_id} not found in system."
    
    return (
        f"Invoice {invoice['invoice_id']}:\n"
        f"  Order ID: {invoice['order_id']}\n"
        f"  Amount: ${invoice['amount']}\n"
        f"  Status: {invoice['status']}\n"
        f"  Payment Method: {invoice['payment_method']}\n"
        f"  Date: {invoice['date']}"
    )


async def check_refund_eligibility(order_id: str) -> str:
    """Check if an order is eligible for refund.
    
    Args:
        order_id: The order identifier
        
    Returns:
        Refund eligibility status and reason
    """
    print(f"[TOOL] check_refund_eligibility called with order_id={order_id}")
    order = ORDERS_DB.get(order_id)
    if not order:
        return f"Order {order_id} not found."
    
    # Simple eligibility logic
    if order['status'] == 'shipped':
        return f"Order {order_id} is eligible for refund within 30 days of delivery."
    elif order['status'] == 'processing':
        return f"Order {order_id} can be cancelled without charge since it hasn't shipped yet."
    else:
        return f"Order {order_id} status is '{order['status']}' - please contact support for refund options."


async def get_tracking_info(tracking_number: str) -> str:
    """Get shipping tracking information.
    
    Args:
        tracking_number: The tracking number
        
    Returns:
        Tracking status and location information
    """
    print(f"[TOOL] get_tracking_info called with tracking_number={tracking_number}")
    
    # Simulated tracking data
    if tracking_number == "TRACK-987654":
        return (
            f"Tracking {tracking_number}:\n"
            f"  Status: In Transit\n"
            f"  Current Location: Denver, CO\n"
            f"  Estimated Delivery: February 12, 2025\n"
            f"  Last Update: February 9, 2025 10:30 AM"
        )
    else:
        return f"Tracking number {tracking_number} not found or not yet active."


async def run_handoff_workflow() -> None:
    """Run a Handoff multi-agent workflow for customer support triage.
    
    Agents:
        - triage_agent: Coordinator that collects basic info and routes to specialists
        - billing_agent: Handles billing, invoices, and payment issues
        - shipping_agent: Handles shipping, tracking, and delivery issues
        - compliance_agent: Reviews and finalizes communications for policy compliance
    """

    # Define the triage agent (coordinator)
    triage_agent = ChatAgent(
        name="triage_agent",
        description=(
            "Customer support triage agent that collects basic information "
            "and routes to appropriate specialists based on the issue type."
        ),
        instructions=(
            "You are the first point of contact for customer support. "
            "Your job is to:\n"
            "1. Greet the customer warmly\n"
            "2. Collect their order ID or invoice ID if relevant\n"
            "3. Understand their issue (billing, shipping, or general inquiry)\n"
            "4. Route to the appropriate specialist:\n"
            "   - Use handoff_to_billing_agent for payment, invoice, or refund issues\n"
            "   - Use handoff_to_shipping_agent for delivery, tracking, or shipping issues\n"
            "5. If the issue is simple and doesn't need a specialist, help directly\n"
            "\n"
            "Be concise and friendly. Always confirm you understand the issue before handing off."
        ),
        chat_client=small_client,
        tools=[lookup_order, lookup_invoice],
    )

    # Define the billing specialist agent
    billing_agent = ChatAgent(
        name="billing_agent",
        description=(
            "Billing specialist that handles payment issues, invoices, and refunds."
        ),
        instructions=(
            "You are a billing specialist. Your responsibilities:\n"
            "1. Review invoice and payment details\n"
            "2. Check refund eligibility when requested\n"
            "3. Explain billing charges clearly\n"
            "4. Process refund requests (simulated)\n"
            "5. After resolving the billing issue, hand off to compliance_agent "
            "to ensure your response meets company policy standards\n"
            "\n"
            "Use your tools to look up invoice details and check refund eligibility. "
            "Be professional and empathetic, especially when dealing with payment disputes."
        ),
        chat_client=medium_client,
        tools=[lookup_invoice, check_refund_eligibility, lookup_order],
    )

    # Define the shipping specialist agent
    shipping_agent = ChatAgent(
        name="shipping_agent",
        description=(
            "Shipping specialist that handles delivery, tracking, and shipping issues."
        ),
        instructions=(
            "You are a shipping specialist. Your responsibilities:\n"
            "1. Provide tracking information and delivery updates\n"
            "2. Explain shipping delays or issues\n"
            "3. Advise on shipping options and policies\n"
            "4. After resolving the shipping issue, hand off to compliance_agent "
            "to ensure your response meets company policy standards\n"
            "\n"
            "Use your tools to look up order and tracking details. "
            "Be clear about delivery timelines and proactive about resolving concerns."
        ),
        chat_client=medium_client,
        tools=[lookup_order, get_tracking_info],
    )

    # Define the compliance/policy agent
    compliance_agent = ChatAgent(
        name="compliance_agent",
        description=(
            "Compliance agent that reviews specialist responses to ensure they meet "
            "company policy and communication standards."
        ),
        instructions=(
            "You are a compliance specialist. Your job is to:\n"
            "1. Review the conversation and solution provided by specialists\n"
            "2. Ensure the response aligns with company policies\n"
            "3. Add any necessary disclaimers or policy reminders\n"
            "4. Provide a polished, final response to the customer\n"
            "5. End the conversation with clear next steps\n"
            "\n"
            "Be thorough but don't contradict the specialist unless there's a clear policy violation. "
            "Your goal is to add a final layer of quality assurance."
        ),
        chat_client=completion_client,
    )

    print("\n---------------------------------------------------------------------")
    print("\nBuilding Handoff Workflow...")
    print("\n---------------------------------------------------------------------")

    # Build the Handoff workflow
    # The coordinator (triage_agent) can hand off to specialists
    # Specialists can then hand off to compliance_agent
    workflow = (
        HandoffBuilder(
            name="customer_support_handoff",
            participants=[triage_agent, billing_agent, shipping_agent, compliance_agent],
        )
        .set_coordinator("triage_agent")
        .with_interaction_mode("autonomous")  # Run without human intervention
        .build()
    )

    # Example customer query
    task = (
        "Hello, I need help with my order ORD-12345. "
        "I was charged but haven't received my package yet. "
        "Can you help me track it and possibly get a refund?"
    )

    print(f"\nCustomer Query: {task}")
    print("\nStarting workflow execution...")
    print("\n[Triage Agent will collect info and hand off to appropriate specialist]\n")
    
    try:
        # Wrap the workflow as an agent and run it
        print("\nRunning Handoff workflow...\n")
        workflow_agent = workflow.as_agent(name="SupportWorkflowAgent")
        
        async for response in workflow_agent.run_stream(task):
            # Print streaming response text
            print(response.text, end="", flush=True)

        print(f"\n\n[Workflow completed!]")
        print("\nObservations:")
        print("  - Triage agent collected order ID")
        print("  - Determined this is both a tracking AND billing issue")
        print("  - Handed off to appropriate specialist(s)")
        print("  - Specialist(s) resolved the issue using their tools")
        print("  - Compliance agent reviewed and finalized the response")
        
    except Exception as e:
        # Handle any errors during workflow execution
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        print(f"Workflow execution failed: {e}")


async def main() -> None:
    """Entry point for the Handoff workflow application.
    
    This function serves as the main entry point and orchestrates
    the execution of the Handoff multi-agent workflow.
    """
    await run_handoff_workflow()


# Script entry point
# When run as a script (not imported), execute the main async function
if __name__ == "__main__":
    asyncio.run(main())
