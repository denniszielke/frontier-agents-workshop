# Copyright (c) Microsoft. All rights reserved.
import sys
from pathlib import Path

# Add the project root to the path so we can import from samples.shared
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from samples.shared.model_client import create_chat_client
"""Simple AG-UI server example."""

import os

from agent_framework import ChatAgent
from agent_framework_ag_ui import add_agent_framework_fastapi_endpoint

from fastapi import FastAPI

from dotenv import load_dotenv

load_dotenv()

medium_model_name = os.environ.get("MEDIUM_DEPLOYMENT_MODEL_NAME")

medium_client=create_chat_client(medium_model_name)

# Create the AI agent
agent = ChatAgent(
    name="AGUIAssistant",
    instructions="You are a helpful assistant.",
    chat_client=medium_client,
)

# Create FastAPI app
app = FastAPI(title="AG-UI Server")

# Register the AG-UI endpoint
add_agent_framework_fastapi_endpoint(app, agent, "/")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8888)