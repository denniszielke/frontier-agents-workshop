import asyncio
import logging
from datetime import datetime

import pytz
import uvicorn
from dotenv import load_dotenv
from fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("WeatherTimeSpace")

mcp = FastMCP("WeatherTimeSpace")

# Use Streamable HTTP transport (recommended for web deployments)
streamable_http_app = mcp.http_app(path="/mcp", transport="streamable-http")


# Six popular locations mapped to IANA time zones
LOCATIONS = {
    "Seattle": "America/Los_Angeles",
    "New York": "America/New_York",
    "London": "Europe/London",
    "Berlin": "Europe/Berlin",
    "Tokyo": "Asia/Tokyo",
    "Sydney": "Australia/Sydney",
}


# Static weather descriptions per time-of-day bucket
# morning: 05-11, afternoon: 12-17, evening: 18-21, night: 22-04
STATIC_WEATHER = {
    "morning": "Cool and clear with a light breeze.",
    "afternoon": "Mild temperatures with scattered clouds and good visibility.",
    "evening": "Calm conditions with a gentle breeze and fading light.",
    "night": "Quiet, mostly clear skies and cooler air.",
}


def _get_time_bucket(local_dt: datetime) -> str:
    hour = local_dt.hour
    if 5 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "afternoon"
    if 18 <= hour <= 21:
        return "evening"
    return "night"


def _normalize_location(name: str) -> str:
    name = name.strip().lower()
    for key in LOCATIONS.keys():
        if name == key.lower():
            return key
    # fallback: first word capitalized
    return name.title()


@mcp.resource("config://version")
def get_version() -> dict:
    return {
        "version": "1.0.0",
        "features": ["tools", "resources"],
    }


@mcp.tool()
def list_supported_locations() -> list[str]:
    """List the six popular locations that this server supports."""
    logger.info("Tool called: list_supported_locations")
    result = list(LOCATIONS.keys())
    logger.info(f"Returning {len(result)} supported locations")
    return result


@mcp.tool()
def get_weather_at_location(location: str) -> str:
    """Get a static weather description for a supported location based on the current local time there.

    The response depends on the time of day at the location (morning, afternoon, evening, night)
    but is otherwise deterministic and not based on live data.
    """
    logger.info(f"Tool called: get_weather_at_location(location='{location}')")
    norm = _normalize_location(location)
    if norm not in LOCATIONS:
        return "Unsupported location. Use `list_supported_locations` to see valid options."

    tz_name = LOCATIONS[norm]
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        return "Sorry, I couldn't resolve the time zone for that location."

    now_local = datetime.now(tz)
    bucket = _get_time_bucket(now_local)
    description = STATIC_WEATHER[bucket]

    local_time_str = now_local.strftime("%Y-%m-%d %H:%M")

    result = (
        f"Weather for {norm} at {local_time_str} ({bucket}): "
        f"{description}"
    )
    logger.info(f"Returning weather for {norm}: {bucket}")
    return result


@mcp.tool()
def get_weather_for_multiple_locations(locations: list[str]) -> list[str]:
    """Get static weather for multiple supported locations at their current local times."""
    logger.info(f"Tool called: get_weather_for_multiple_locations(locations={locations})")
    results: list[str] = []
    for loc in locations:
        results.append(get_weather_at_location(loc))
    logger.info(f"Returning weather for {len(results)} locations")
    return results


@mcp.prompt()
def describe_weather_capabilities() -> list[base.Message]:
    """Explain how to use this MCP server to get time-of-day based weather for popular locations."""

    return [
        base.Message(
            role="user",
            content=[
                base.TextContent(
                    text=(
                        "You are connected to a weather MCP server that provides "
                        "static weather descriptions for six popular locations. "
                        "Explain how to: (1) list supported locations, (2) get the "
                        "weather for a single location at its current local time, and "
                        "(3) fetch weather for multiple locations at once."
                    )
                )
            ],
        )
    ]


async def check_mcp(mcp: FastMCP):
    tools = await mcp.get_tools()
    resources = await mcp.get_resources()
    templates = await mcp.get_resource_templates()

    print(f"{len(tools)} Tool(s): {', '.join([t.name for t in tools.values()])}")
    print(
        f"{len(resources)} Resource(s): {', '.join([r.name for r in resources.values()])}"
    )
    print(
        f"{len(templates)} Resource Template(s): {', '.join([t.name for t in templates.values()])}"
    )

    return mcp


if __name__ == "__main__":
    try:
        asyncio.run(check_mcp(mcp))
        uvicorn.run(streamable_http_app, host="0.0.0.0", port=8001)
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Cleaning up...")
    except Exception as e:
        print(f"An error occurred: {e}")
