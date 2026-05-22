import click
import uvicorn
import sys
import os
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from a2a.server.agent_execution import AgentExecutor
from a2a.server.routes import create_rest_routes, create_jsonrpc_routes, create_agent_card_routes
from a2a.server.request_handlers.default_request_handler import (
    LegacyRequestHandler,
)
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import (
    SendMessageRequest,
    SendMessageResponse,
)
from samples.a2a_communication.server.weather_agent_executor import WeatherAgentExecutor, weather_agent_card

class A2ARequestHandler(LegacyRequestHandler):
    """A2A Request Handler for the A2A Repo Agent."""

    async def on_message_send(
        self, request: SendMessageRequest, *args, **kwargs
    ) -> SendMessageResponse:
        return await super().on_message_send(request, *args, **kwargs)


@click.command()
@click.option('--host', 'host', default='0.0.0.0')
@click.option('--port', 'port', default=8080)
def main(host: str, port: int):
    """Start the weather Q&A agent server backed by HelloWorldAgentExecutor."""


    task_store = InMemoryTaskStore()

    if os.environ.get("CONTAINER_APP_NAME") and os.environ.get("CONTAINER_APP_ENV_DNS_SUFFIX"):
        url = f'https://{os.environ["CONTAINER_APP_NAME"]}.{os.environ["CONTAINER_APP_ENV_DNS_SUFFIX"]}'
    elif os.environ.get("A2A_AGENT_HOST"):
        url = os.environ["A2A_AGENT_HOST"]
    else:
        url = f'http://{host}:{port}/'

    agent_card = weather_agent_card(url=url)

    request_handler = A2ARequestHandler(
        agent_executor=WeatherAgentExecutor(),
        task_store=task_store,
        agent_card=agent_card,
    )

    routes = create_agent_card_routes(agent_card) + create_jsonrpc_routes(request_handler, rpc_url="/") + create_rest_routes(request_handler)

    async def healthz(request):
        return JSONResponse({"status": "ok"})

    routes.append(Route("/_healthz", endpoint=healthz))

    app = Starlette(routes=routes)

    uvicorn.run(app, host=host, port=port)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        sys.exit(0)