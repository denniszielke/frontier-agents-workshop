import os
import logging
from random import randint
from typing import Annotated, override

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.helpers import new_text_message, new_task, new_text_artifact
from agent_framework import ChatOptions, Message
from samples.shared.model_client import create_chat_client as _create_openai_client
from dotenv import load_dotenv

from pydantic import Field


load_dotenv()

model_name = os.environ["COMPLETION_DEPLOYMENT_NAME"]


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("agent-executor")

def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Simple weather tool returning fake conditions for a location."""
    conditions = ["sunny", "cloudy", "rainy", "stormy"]
    return f"The weather in {location} is {conditions[randint(0, 3)]} with a high of {randint(10, 30)}°C."


def weather_agent_card(url: str) -> AgentCard:
    """Define the agent card for the weather Q&A agent."""
    skill = AgentSkill(
        id='answer_weather_questions',
        name='Answer questions about the weather',
        description=(
            'The agent can answer simple questions about the weather '
            'for given locations using a weather tool.'
        ),
        tags=['weather', 'q&a'],
        examples=[
            'What is the weather in Amsterdam?',
            'What is the weather like in Paris and Berlin?',
        ],
    )

    agent_card = AgentCard(
        name='Weather Q&A Agent',
        description=(
            'A simple weather question answering agent that uses a tool '
            'to respond with current-like conditions for requested locations.'
        ),
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(
            streaming=False,
        ),
        skills=[skill],
    )
    return agent_card


class WeatherAgentExecutor(AgentExecutor):
    """Simple weather Q&A agent using Microsoft agent framework."""

    def __init__(self):
        # Reuse the same authentication logic as the basic agent sample
        logging.info("Creating OpenAIChatClient for WeatherAgentExecutor with model %s", model_name)
        self.agent = _create_openai_client(model_name)

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task = context.current_task

        if not context.message:
            raise Exception('No message provided')

        if not task:
            task = new_task(context.task_id, context.context_id, TaskState.TASK_STATE_SUBMITTED)
            await event_queue.enqueue_event(task)

        # Use the Microsoft agent framework chat client with the weather tool.
        # We do a single-turn completion and treat the result as the final task artifact.
        user_input = context.get_user_input()
        messages = [
            Message(role="system", contents=["You are a weather expert. Help the user with their input using the tools you have available."]),
            Message(role="user", contents=[user_input]),
        ]
        options = ChatOptions(tools=[get_weather])

        # get_response may return a rich object; coerce to string for A2A
        response = await self.agent.get_response(messages, options=options)

        # Ensure the artifact text is always a plain string
        response_text = str(response)

        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                append=False,
                context_id=task.context_id,
                task_id=task.id,
                last_chunk=True,
                artifact=new_text_artifact(
                    name='current_result',
                    description='Result of request to weather agent.',
                    text=response_text,
                ),
            )
        )
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(state=TaskState.TASK_STATE_COMPLETED),
                context_id=task.context_id,
                task_id=task.id,
            )
        )

    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')