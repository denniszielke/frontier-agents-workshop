# Exercise: Handoff Orchestration Basics

This exercise demonstrates the Handoff orchestration pattern - a multi-agent coordination approach that models real-world escalation and handover workflows. Unlike Magentic's intelligent orchestrator, Handoff uses explicit agent-to-agent control transfer where agents themselves decide when to pass responsibility.

## Handoff vs. Magentic

### Handoff Pattern
- **Explicit control transfer**: Agents explicitly hand off control to other agents
- **Agent-driven routing**: Individual agents decide when and to whom to transfer
- **Context preservation**: Full conversation history flows through all handoffs
- **Real-world escalation**: Models support tickets, case routing, and specialist workflows
- **No central orchestrator**: Distributed decision-making

### Magentic Pattern
- **Intelligent orchestration**: A dedicated manager agent coordinates all activity
- **Centralized planning**: Manager decides which agent acts next based on global context
- **Task decomposition**: Breaks complex problems into subtasks automatically
- **Adaptive workflow**: Manager can invoke any agent multiple times in any order
- **Central orchestrator**: Single point of control and decision-making

### When to Use Each

**Use Handoff when:**
- You have clear escalation paths (e.g., customer support tiers)
- Specialists need full control within their domain
- The workflow mimics real-world handover processes
- Each agent has exclusive responsibilities

**Use Magentic when:**
- Tasks require dynamic decomposition and planning
- You need adaptive, iterative problem-solving
- The solution path is not predefined
- Multiple agents may need to collaborate on sub-problems

## This Sample: Customer Support Triage

This example demonstrates a customer support workflow with:

1. **Triage Agent (Coordinator)**: 
   - Greets customers and collects basic information
   - Identifies the issue type (billing vs. shipping)
   - Routes to the appropriate specialist via explicit handoff

2. **Billing Specialist Agent**:
   - Handles payment, invoice, and refund issues
   - Checks refund eligibility
   - Hands off to compliance for final review

3. **Shipping Specialist Agent**:
   - Handles delivery, tracking, and shipping issues
   - Provides tracking updates
   - Hands off to compliance for final review

4. **Compliance Agent**:
   - Reviews specialist responses for policy compliance
   - Adds disclaimers and ensures quality
   - Provides final polished response to customer

### Tools Used
- `lookup_order`: Retrieve order details by order ID
- `lookup_invoice`: Retrieve invoice details by invoice ID
- `check_refund_eligibility`: Check if an order qualifies for refund
- `get_tracking_info`: Get shipping tracking updates

## Key Concepts

1. **HandoffBuilder**: API for building handoff workflows
2. **Coordinator Agent**: Entry point that routes to specialists
3. **Specialist Agents**: Domain experts with specific responsibilities
4. **Autonomous Mode**: Workflow runs without human intervention
5. **Context Flow**: Conversation history preserved across all handoffs

## Prerequisites

- `.env` file configured with your LLM endpoint details
- Agent Framework installed: `pip install -r requirements.txt`
- Environment variables:
  - `COMPLETION_DEPLOYMENT_NAME`: Model for complex reasoning (compliance agent)
  - `MEDIUM_DEPLOYMENT_MODEL_NAME`: Model for specialists
  - `SMALL_DEPLOYMENT_MODEL_NAME`: Model for triage

## Setup

1. Clone the repository (if you haven't already).

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .agentic
   source .agentic/bin/activate  # On Windows use `.agentic\Scripts\activate`
   pip install -r requirements.txt
   ```

   If you already have the agent-framework installed globally or followed the main README guidance, you can skip this step.

3. Configure your `.env` file with the necessary API keys and model settings. Example:

   ```
   COMPLETION_DEPLOYMENT_NAME=gpt-4o
   MEDIUM_DEPLOYMENT_MODEL_NAME=gpt-4o-mini
   SMALL_DEPLOYMENT_MODEL_NAME=gpt-4o-mini
   
   # For Azure OpenAI
   AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key
   
   # OR for GitHub Models
   GITHUB_TOKEN=your-github-token
   ```

4. Run the Handoff orchestration script from the repository's root folder:
   
   ```bash
   python samples/handoff/main.py
   ```

5. Observe the console output for handoff events, tool calls, and agent responses.

## What to Observe

When running the sample, watch for:

### 1. Explicit Handoff Decisions
- The triage agent explicitly decides to hand off to a specialist
- You'll see log messages indicating handoff tool calls
- Each handoff includes the full context of the conversation

### 2. Specialist-Only Responsibilities
- **Billing agent**: Only activates for payment/refund issues
- **Shipping agent**: Only activates for tracking/delivery issues
- **Compliance agent**: Only activates for final review

### 3. Tool Usage by Domain
- Each specialist has access to only their relevant tools
- Triage agent uses `lookup_order` and `lookup_invoice` for initial investigation
- Specialists use domain-specific tools (`check_refund_eligibility`, `get_tracking_info`)

### 4. Context Preservation
- Information collected by triage agent is available to specialists
- Specialists' work is visible to compliance agent
- No information is lost during handoffs

### 5. Sequential Flow (not parallel)
- Unlike concurrent workflows, handoff is sequential
- Only one agent is active at a time
- Clear chain of responsibility

## Example Output

```
Customer Query: Hello, I need help with my order ORD-12345...

[TOOL] lookup_order called with order_id=ORD-12345
[Triage Agent]: I can see your order. This involves both tracking and potential refund...
[Handoff to shipping_agent]

[TOOL] get_tracking_info called with tracking_number=TRACK-987654
[Shipping Agent]: Your package is in transit, estimated delivery Feb 12...
[Handoff to compliance_agent]

[Compliance Agent]: Let me review the response and add our standard policies...
[Final Response]: Your package is on the way. If it doesn't arrive by Feb 15, 
                  you're eligible for a full refund under our delivery guarantee...
```

## Customization Ideas

- Add more specialist agents (technical support, returns, sales)
- Implement multi-level handoffs (Level 1 → Level 2 support)
- Add human-in-the-loop mode for manager approval
- Connect real databases instead of mock data
- Add sentiment analysis to route escalations
- Implement agent capabilities based on customer tier (VIP routing)

## Reference

- Microsoft Learn: [Handoff Orchestration Pattern](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/orchestrations/handoff?pivots=programming-language-python)
- API Reference: [HandoffBuilder](https://learn.microsoft.com/en-us/python/api/agent-framework-core/agent_framework.handoffbuilder)
- Comparison: See `samples/magentic/` for the Magentic orchestration pattern
