"""Magentic Workflow Example.

This module demonstrates a multi-agent workflow using the Magentic framework.
It orchestrates two specialized agents (Researcher and Coder) to collaboratively
solve complex tasks that require both information gathering and computational analysis.

The example workflow:
1. A ResearcherAgent gathers information from various sources
2. A CoderAgent performs data processing and quantitative analysis
3. A standard manager orchestrates the collaboration between agents
4. Events are streamed in real-time to provide visibility into the workflow

Requirements:
- Azure OpenAI service configured with appropriate credentials
- Environment variables loaded from .env file
- Azure CLI authentication configured
"""

import asyncio
import logging

from dotenv import load_dotenv
from agent_framework import (
    ChatAgent,
    ChatMessage,
    HostedCodeInterpreterTool,
    MagenticAgentDeltaEvent,
    MagenticAgentMessageEvent,
    MagenticBuilder,
    MagenticFinalResultEvent,
    MagenticOrchestratorMessageEvent,
    WorkflowEvent,
)
from agent_framework.azure import AzureOpenAIChatClient, AzureOpenAIResponsesClient 
from azure.identity import AzureCliCredential

# Configure logging to debug level for detailed workflow tracking
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables from .env file (e.g., Azure credentials, endpoints)
load_dotenv()

logger.info("Environment variables loaded successfully")


async def run_magentic_workflow() -> None:
    """Run a Magentic multi-agent workflow for energy efficiency analysis.
    
    This function demonstrates a complete Magentic workflow that:
    1. Creates specialized agents (Researcher and Coder)
    2. Configures a workflow manager to orchestrate agent collaboration
    3. Executes a complex task requiring both research and computation
    4. Streams real-time events showing workflow progress
    
    The workflow analyzes energy efficiency of ML model architectures,
    requiring both information gathering (research) and quantitative
    analysis (code execution).
    
    Raises:
        Exception: If workflow execution fails due to API errors,
                   authentication issues, or agent execution problems.
    """
    
    # Create the ResearcherAgent: specializes in finding and gathering information
    # This agent works better with gpt-4o-search-preview model capabilities for web searches
    researcher_agent = ChatAgent(
        name="ResearcherAgent",
        description="Specialist in research and information gathering",
        instructions=(
            "You are a Researcher. You find information without additional computation or quantitative analysis."
        ),
        # Azure OpenAI client with CLI-based authentication
        chat_client=AzureOpenAIChatClient(credential=AzureCliCredential()),
    )

    # Create the CoderAgent: specializes in writing and executing code
    # This agent can perform computations, data analysis, and generate visualizations
    coder_agent = ChatAgent(
        name="CoderAgent",
        description="A helpful assistant that writes and executes code to process and analyze data.",
        instructions="You solve questions using code. Please provide detailed analysis and computation process.",
        # Azure OpenAI Responses client for chat completion
        chat_client=AzureOpenAIResponsesClient(credential=AzureCliCredential()),
        # HostedCodeInterpreterTool enables secure Python code execution in a sandbox
        tools=HostedCodeInterpreterTool(),
    )
    
    # State variables for managing streaming display output
    # These track which agent is currently streaming and whether a line is open
    last_stream_agent_id: str | None = None  # ID of the agent that last sent a delta
    stream_line_open: bool = False  # Whether we're currently in the middle of streaming

    # Unified callback for all workflow events
    def on_event(event: WorkflowEvent) -> None:
        """Process and display events emitted by the Magentic workflow.
        
        This callback handles multiple event types to provide real-time visibility
        into workflow execution:
        
        - MagenticOrchestratorMessageEvent: Messages from the workflow manager
        - MagenticAgentDeltaEvent: Streaming token-by-token agent responses
        - MagenticAgentMessageEvent: Complete agent messages
        - MagenticFinalResultEvent: Final workflow result
        
        Args:
            event: A workflow event of any supported type.
        
        Note:
            This function modifies nonlocal variables to track streaming state
            and provide continuous output formatting.
        """
        nonlocal last_stream_agent_id, stream_line_open
        
        # Handle orchestrator messages (workflow coordination events)
        if isinstance(event, MagenticOrchestratorMessageEvent):
            print(f"\n[ORCH:{event.kind}]\n\n{getattr(event.message, 'text', '')}\n{'-' * 26}")
            
        # Handle streaming delta events (token-by-token agent responses)
        elif isinstance(event, MagenticAgentDeltaEvent):
            # Start a new stream line if agent changed or no stream is currently open
            if last_stream_agent_id != event.agent_id or not stream_line_open:
                if stream_line_open:
                    print()  # Close previous stream line
                print(f"\n[STREAM:{event.agent_id}]: ", end="", flush=True)
                last_stream_agent_id = event.agent_id
                stream_line_open = True
            # Print the delta text without newline for continuous streaming
            print(event.text, end="", flush=True)
            
        # Handle complete agent message events
        elif isinstance(event, MagenticAgentMessageEvent):
            # Close any open stream line before showing final message
            if stream_line_open:
                print(" (final)")  # Mark end of streaming
                stream_line_open = False
                print()
            # Display the complete agent message
            msg = event.message
            if msg is not None:
                # Flatten newlines for compact display
                response_text = (msg.text or "").replace("\n", " ")
                print(f"\n[AGENT:{event.agent_id}] {msg.role.value}\n\n{response_text}\n{'-' * 26}")
                
        # Handle final result event (workflow completion)
        elif isinstance(event, MagenticFinalResultEvent):
            print("\n" + "=" * 50)
            print("FINAL RESULT:")
            print("=" * 50)
            if event.message is not None:
                print(event.message.text)
            print("=" * 50)


    print("\n---------------------------------------------------------------------")
    print("\nBuilding Magentic Workflow...")
    print("\n---------------------------------------------------------------------")
    
    # Build the Magentic workflow using the builder pattern
    workflow = (
        MagenticBuilder()
        # Register the agents as participants in the workflow
        .participants(researcher=researcher_agent, coder=coder_agent)
        # Configure the standard manager to orchestrate agent collaboration
        .with_standard_manager(
            chat_client=AzureOpenAIChatClient(credential=AzureCliCredential()),
            max_round_count=6,  # Maximum conversation rounds before timeout
            max_stall_count=2,   # Max rounds without progress before intervention
            max_reset_count=1,   # Max times workflow can be reset on failure
        )
        # Build the final workflow instance
        .build()
    )
    
    # Define the complex task that requires both research and computation
    # This task demonstrates the need for multi-agent collaboration:
    # - Researcher: Gathers information about ML models, datasets, and energy metrics
    # - Coder: Performs calculations, creates tables, and generates recommendations
    task = (
        "I am preparing a report on the energy efficiency of different machine learning model architectures. "
        "Compare the estimated training and inference energy consumption of ResNet-50, BERT-base, and GPT-2 "
        "on standard datasets (e.g., ImageNet for ResNet, GLUE for BERT, WebText for GPT-2). "
        "Then, estimate the CO2 emissions associated with each, assuming training on an Azure Standard_NC6s_v3 "
        "VM for 24 hours. Provide lists for clarity, and recommend the most energy-efficient model "
        "per task type (image classification, text classification, and text generation)."
    ) 

    print(f"\nTask: {task}")
    print("\nStarting workflow execution...")
    
    try:
        # Execute the workflow with streaming enabled
        # This returns an async generator yielding events as they occur
        async for event in workflow.run_stream(task):
            # Process each event
            on_event(event)

        print(f"Workflow completed!")
    except Exception as e:
        # Handle any errors during workflow execution
        logger.error(f"Workflow execution failed: {e}", exc_info=True)
        print(f"Workflow execution failed: {e}")

async def main() -> None:
    """Entry point for the Magentic workflow application.
    
    This function serves as the main entry point and orchestrates
    the execution of the Magentic multi-agent workflow.
    """
    await run_magentic_workflow()


# Script entry point
# When run as a script (not imported), execute the main async function
if __name__ == "__main__":
    asyncio.run(main())