"""AG-UI client example."""

import asyncio
import os

from agent_framework import Agent
from agent_framework_ag_ui import AGUIChatClient

from dotenv import load_dotenv

load_dotenv()

async def main():
    """Main client loop."""
    # Get server URL from environment or use default
    server_url = os.environ.get("AGUI_SERVER_URL", "http://127.0.0.1:8888/")
    print(f"Connecting to AG-UI server at: {server_url}\n")

    # Create AG-UI chat client
    chat_client = AGUIChatClient(endpoint=server_url)

    # Create agent with the chat client
    agent = Agent(
        chat_client,
        name="ClientAgent",
        instructions="You are a helpful assistant.",
    )

    # Get a session for conversation continuity
    session = agent.create_session()

    try:
        while True:
            # Get user input
            message = input("\nUser (:q or quit to exit): ")
            if not message.strip():
                print("Request cannot be empty.")
                continue

            if message.lower() in (":q", "quit"):
                break

            # Stream the agent response
            print("\nAssistant: ", end="", flush=True)
            async for update in agent.run(message, stream=True, session=session):
                # Print text content as it streams
                if update.text:
                    print(f"\033[96m{update.text}\033[0m", end="", flush=True)

            print("\n")

    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n\033[91mAn error occurred: {e}\033[0m")


if __name__ == "__main__":
    asyncio.run(main())