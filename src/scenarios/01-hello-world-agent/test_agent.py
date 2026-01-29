# Copyright (c) Microsoft. All rights reserved.
"""
Test script for Time & Weather Agent

Runs the 5 test queries from the specification to validate the agent.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from samples.shared.model_client import create_chat_client

import os
import asyncio

from agent_framework import ChatAgent, MCPStreamableHTTPTool

from dotenv import load_dotenv

load_dotenv()

# Configuration
USER_MCP_URL = os.environ.get("USER_MCP_URL", "http://localhost:8002/mcp")
WEATHER_MCP_URL = os.environ.get("WEATHER_MCP_URL", "http://localhost:8001/mcp")

SYSTEM_INSTRUCTIONS = """You are a helpful time and weather assistant. Your capabilities include:

1. **Location Awareness**: 
   - When users mention their location, remember it for the conversation.
   - If the user says they "moved to" a new location, update your understanding.
   - When asked where they are, recall their most recently stated location.

2. **Weather Information**:
   - Use the weather MCP server for weather (supported: Seattle, New York, London, Berlin, Tokyo, Sydney).
   - If the user asks about weather "here", use their remembered location.

3. **Time Information**:
   - Use the user MCP server for time queries.
   - Map city names to timezone format (London → Europe/London, Berlin → Europe/Berlin).
   - If the user asks about time "for me", use their remembered location.

Remember the conversation history to recall user's stated location."""


async def run_tests():
    """Run all 5 spec queries and validate responses."""
    
    model = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME") or os.environ.get("COMPLETION_DEPLOYMENT_NAME")
    print(f"Using model: {model}")
    
    client = create_chat_client(model)
    
    user_mcp = MCPStreamableHTTPTool(name="User Server", url=USER_MCP_URL)
    weather_mcp = MCPStreamableHTTPTool(name="Weather Server", url=WEATHER_MCP_URL)
    
    async with ChatAgent(
        chat_client=client,
        name="TimeWeatherAgent",
        instructions=SYSTEM_INSTRUCTIONS,
        tools=[user_mcp, weather_mcp],
    ) as agent:
        thread = agent.get_new_thread()
        
        # Test queries from spec
        queries = [
            "I am currently in London",
            "What is the weather now here?",
            "What time is it for me right now?",
            "I moved to Berlin, what is the weather like today?",
            "Can you remind me where I said I am based?",
        ]
        
        print("\n" + "=" * 60)
        print("TIME & WEATHER AGENT - SPEC VALIDATION TEST")
        print("=" * 60)
        
        results = []
        for i, query in enumerate(queries, 1):
            print(f"\n--- Query {i}/5 ---")
            print(f"User: {query}")
            
            result = await agent.run(query, thread=thread)
            print(f"Agent: {result.text}")
            results.append((query, result.text))
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        # Basic validation checks
        checks = [
            ("Location acknowledged", "london" in results[0][1].lower()),
            ("Weather returned", "weather" in results[1][1].lower() or "temperature" in results[1][1].lower() or "clear" in results[1][1].lower() or "cloud" in results[1][1].lower()),
            ("Time returned", any(x in results[2][1].lower() for x in ["time", ":", "am", "pm", "o'clock"])),
            ("Berlin weather", "berlin" in results[3][1].lower()),
            ("Location recalled", "berlin" in results[4][1].lower()),
        ]
        
        all_passed = True
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {check_name}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("⚠️  SOME TESTS FAILED - Review responses above")
        print("=" * 60)
        
        return all_passed


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
