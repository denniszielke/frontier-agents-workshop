
import os
import logging

from agent_framework import BaseChatClient
from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient
from agent_framework.foundry import FoundryChatClient

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Configure logging for this sample module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

def create_chat_client(model_name: str) -> BaseChatClient:
    """Create a chat client based on available environment variables.

    Priority order:
    1. FOUNDRY_PROJECT_ENDPOINT - uses FoundryChatClient with DefaultAzureCredential
    2. AZURE_OPENAI_ENDPOINT - uses FoundryChatClient with API key or AAD auth
    3. GITHUB_TOKEN - uses OpenAIChatClient with GitHub Models
    """

    token: str
    endpoint: str

    if (not model_name) or model_name.strip() == "":
        logger.error("Model name is missing. Set COMPLETION_DEPLOYMENT_NAME in your .env file.")
        raise Exception(
            "Model name for OpenAIChatClient is not set. Please set COMPLETION_DEPLOYMENT_NAME in your .env file."
        )

    foundry_endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()

    # Strip "openai/" prefix if present — it's a GitHub Models convention,
    # not valid for Foundry/Azure OpenAI connections.
    foundry_model_name = model_name.split("/", 1)[-1] if "/" in model_name else model_name

    if foundry_endpoint:
        print("Using Foundry project endpoint with DefaultAzureCredential.")
        logger.info("FOUNDRY_PROJECT_ENDPOINT found: %s", foundry_endpoint)
        return FoundryChatClient(
            project_endpoint=foundry_endpoint,
            model=foundry_model_name,
            credential=DefaultAzureCredential(),
        )

    if azure_endpoint:
        logger.info("AZURE_OPENAI_ENDPOINT found: %s", azure_endpoint)

        if azure_api_key:
            print("Using Azure OpenAI API key authentication via Foundry.")
            logger.info("AZURE_OPENAI_API_KEY found - using API key authentication.")
            return FoundryChatClient(
                project_endpoint=azure_endpoint,
                model=foundry_model_name,
                credential=azure_api_key,
            )
        
        else:
            print("Using Azure OpenAI AAD authentication via Foundry.")
            logger.info("AZURE_OPENAI_API_KEY not found - will use AAD authentication.")
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            return FoundryChatClient(
                project_endpoint=azure_endpoint,
                model=foundry_model_name,
                credential=token_provider,
            )

    if github_token:
        print("Using GitHub Models endpoint with token authentication.")
        logger.info("Using GitHub Models endpoint with token authentication.")
        token = github_token
        endpoint = "https://models.github.ai/inference"
        async_openai_client = AsyncOpenAI(
            base_url=endpoint,
            api_key=token
        )

        return OpenAIChatCompletionClient(
            model=model_name if "/" in model_name else "openai/" + model_name,
            async_client=async_openai_client,
        )
    