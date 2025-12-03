
import os
import logging

from agent_framework import BaseChatClient
from agent_framework.openai import OpenAIChatClient 
from agent_framework.azure import AzureOpenAIChatClient

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
    """Create an OpenAIChatClient."""

    token: str
    endpoint: str

    if (not model_name) or model_name.strip() == "":
        logger.error("Model name is missing. Set COMPLETION_DEPLOYMENT_NAME in your .env file.")
        raise Exception(
            "Model name for OpenAIChatClient is not set. Please set COMPLETION_DEPLOYMENT_NAME in your .env file."
        )

    github_token = os.environ.get("GITHUB_TOKEN", "").strip()
    azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()

    if azure_endpoint:
        logger.info("AZURE_OPENAI_ENDPOINT found: %s", azure_endpoint)

        if azure_api_key:
            print("Using Azure OpenAI API key authentication.")
            logger.info("AZURE_OPENAI_API_KEY found - using API key authentication.")
            token = azure_api_key
            endpoint = azure_endpoint
            return AzureOpenAIChatClient(
                deployment_name=model_name,
                azure_api_key=token,
                endpoint=endpoint,
            )   
        
        else:
            print("Using Azure OpenAI AAD authentication.")
            logger.info("AZURE_OPENAI_API_KEY not found - will use AAD authentication.")
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            endpoint = azure_endpoint

            return AzureOpenAIChatClient(
                deployment_name=model_name,
                ad_token_provider=token_provider,
                endpoint=endpoint,
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

        return OpenAIChatClient(
            model_id=model_name,
            async_client=async_openai_client,
        )
    