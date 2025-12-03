import click
import uvicorn

from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers.default_request_handler import (
    DefaultRequestHandler,
)
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import (
    GetTaskRequest,
    GetTaskResponse,
    SendMessageRequest,
    SendMessageResponse,
)

from samples.a2a_communication.server.weather_agent_executor import WeatherAgentExecutor, weather_agent_card


class A2ARequestHandler(DefaultRequestHandler):
    """A2A Request Handler for the A2A Repo Agent."""

    def __init__(
        self, agent_executor: AgentExecutor, task_store: InMemoryTaskStore
    ):
        super().__init__(agent_executor, task_store)

    async def on_get_task(
        self, request: GetTaskRequest, *args, **kwargs
    ) -> GetTaskResponse:
        return await super().on_get_task(request, *args, **kwargs)

    async def on_message_send(
        self, request: SendMessageRequest, *args, **kwargs
    ) -> SendMessageResponse:
        return await super().on_message_send(request, *args, **kwargs)


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=8888)
def main(host: str, port: int):
    """Start the weather Q&A agent server backed by HelloWorldAgentExecutor."""


    task_store = InMemoryTaskStore()
    request_handler = A2ARequestHandler(
        agent_executor=WeatherAgentExecutor(),
        task_store=task_store,
    )

    server = A2AStarletteApplication(
        agent_card=weather_agent_card(url=f'http://{host}:{port}/'), http_handler=request_handler
    )
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == '__main__':
    main()