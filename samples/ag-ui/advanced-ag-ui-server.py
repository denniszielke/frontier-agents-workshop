# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client

"""AG-UI server example with server-side tools."""

import logging
import os

from agent_framework import ChatAgent, ai_function
from agent_framework.ag_ui import add_agent_framework_fastapi_endpoint
from dotenv import load_dotenv
from fastapi import FastAPI

from dotenv import load_dotenv

load_dotenv()

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")

medium_client=create_chat_client(medium_model_name)


# Server-side tool (executes on server)
@ai_function(description="Get the time zone for a location.")
def get_time_zone(location: str) -> str:
    """Get the time zone for a location.

    Args:
        location: The city or location name
    """
    print(f"[SERVER] get_time_zone tool called with location: {location}")
    timezone_data = {
        "seattle": "Pacific Time (UTC-8)",
        "san francisco": "Pacific Time (UTC-8)",
        "new york": "Eastern Time (UTC-5)",
        "london": "Greenwich Mean Time (UTC+0)",
    }
    result = timezone_data.get(location.lower(), f"Time zone data not available for {location}")
    print(f"[SERVER] get_time_zone returning: {result}")
    return result


# Create the AI agent with ONLY server-side tools
# IMPORTANT: Do NOT include tools that the client provides!
# In this example:
# - get_time_zone: SERVER-ONLY tool (only server has this)
# - get_weather: CLIENT-ONLY tool (client provides this, server should NOT include it)
# The client will send get_weather tool metadata so the LLM knows about it,
# and @use_function_invocation on AGUIChatClient will execute it client-side.
# This matches the .NET AG-UI hybrid execution pattern.
agent = ChatAgent(
    name="AGUIAssistant",
    instructions="You are a helpful assistant. Use get_weather for weather and get_time_zone for time zones.",
    chat_client=medium_client,
    tools=[get_time_zone],  # ONLY server-side tools
)

# Create FastAPI app
app = FastAPI(title="AG-UI Server")

# Register the AG-UI endpoint
add_agent_framework_fastapi_endpoint(app, agent, "/")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8888, log_level="debug", access_log=True)