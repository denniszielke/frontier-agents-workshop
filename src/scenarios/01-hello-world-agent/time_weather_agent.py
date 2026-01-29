# Copyright (c) Microsoft. All rights reserved.
"""
Time & Weather Agent - Scenario 01

A conversational agent that:
- Remembers user location from conversation context
- Retrieves weather information via MCP server
- Retrieves current time via MCP server
- Maintains conversation state across multiple turns

Usage:
    1. Start MCP servers:
       - User server: cd src/mcp-server/02-user-server && python server-mcp-sse-user.py
       - Weather server: cd src/mcp-server/04-weather-server && python server-mcp-sse-weather.py
    2. Run this agent: python time_weather_agent.py
    3. Chat with the agent about time and weather

See specs/1-time-weather-agent/quickstart.md for detailed instructions.
"""

import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from samples.shared.model_client import create_chat_client

import os
import asyncio

from agent_framework import ChatAgent, MCPStreamableHTTPTool

from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# Configuration
# =============================================================================

# Model configuration from environment
completion_model_name = os.environ.get("COMPLETION_DEPLOYMENT_NAME")
medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")
small_model_name = os.environ.get("SMALL_DEPLOYMENT_MODEL_NAME")

# MCP Server URLs
USER_MCP_URL = os.environ.get("USER_MCP_URL", "http://localhost:8002/mcp")
WEATHER_MCP_URL = os.environ.get("WEATHER_MCP_URL", "http://localhost:8001/mcp")

# Create chat client (use medium model for better reasoning)
chat_client = create_chat_client(medium_model_name or completion_model_name)

# =============================================================================
# System Instructions
# =============================================================================

SYSTEM_INSTRUCTIONS = """You are a helpful time and weather assistant. Your capabilities include:

1. **Location Awareness**: 
   - When users mention their location (e.g., "I am in London", "I'm currently in Berlin"), 
     remember it for the duration of the conversation.
   - If the user says they "moved to" a new location, update your understanding of their location.
   - When asked where they are, recall their most recently stated location.

2. **Weather Information**:
   - Use the weather MCP server to get weather for supported locations.
   - Supported locations: Seattle, New York, London, Berlin, Tokyo, Sydney.
   - If the user asks about weather "here" or "for me", use their remembered location.
   - If no location is known, politely ask where they are.

3. **Time Information**:
   - Use the user MCP server to get current time for a location.
   - Map city names to timezone format:
     * London → Europe/London
     * Berlin → Europe/Berlin  
     * New York → America/New_York
     * Seattle → America/Los_Angeles
     * Tokyo → Asia/Tokyo
     * Sydney → Australia/Sydney
   - If the user asks about time "for me" or "here", use their remembered location.

4. **Conversation Style**:
   - Be friendly and conversational.
   - Acknowledge when users tell you their location.
   - Proactively offer related information when appropriate.
   - If you don't know the user's location and they ask about weather or time "here", 
     ask them where they are located.

Remember: The conversation history contains all previous messages. Use it to recall 
information the user has shared, like their location."""

# =============================================================================
# Main Agent Logic
# =============================================================================

async def run_conversation() -> None:
    """Run an interactive conversation with the Time & Weather Agent."""
    
    print("=" * 60)
    print("Time & Weather Agent")
    print("=" * 60)
    print("I can help you with time and weather information.")
    print("Tell me where you are, and ask about the weather or time!")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("=" * 60)
    print()

    # Configure MCP tools for user and weather servers
    user_mcp = MCPStreamableHTTPTool(
        name="User Time Server",
        url=USER_MCP_URL,
    )
    
    weather_mcp = MCPStreamableHTTPTool(
        name="Weather Server", 
        url=WEATHER_MCP_URL,
    )

    # Create the agent with both MCP tools
    async with ChatAgent(
        chat_client=chat_client,
        name="TimeWeatherAgent",
        instructions=SYSTEM_INSTRUCTIONS,
        tools=[user_mcp, weather_mcp],
    ) as agent:
        
        # Create a thread to maintain conversation history
        thread = agent.get_new_thread()
        
        # Conversation loop
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ("quit", "exit", "q"):
                    print("\nGoodbye! Stay weather-aware! 🌤️")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Run the agent with the user's message, using the thread for memory
                result = await agent.run(user_input, thread=thread)
                
                # Display the agent's response
                print(f"\nAgent: {result.text}\n")
                
            except KeyboardInterrupt:
                print("\n\nConversation interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Please try again or check if MCP servers are running.\n")


async def main() -> None:
    """Entry point for the Time & Weather Agent."""
    await run_conversation()


if __name__ == "__main__":
    asyncio.run(main())
