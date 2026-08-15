import webbrowser
import urllib.parse
from typing import Dict, Any
from app.tools.registry import tool_registry
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.tools.browser")

@tool_registry.register(
    name="open_url",
    description="Open a website URL in the user's default web browser.",
    parameters={
        "url": {
            "type": "string",
            "description": "Full URL to open (e.g. 'https://youtube.com', 'https://github.com')."
        }
    },
    required=["url"],
    risk_level=0
)
def open_url(url: str) -> Dict[str, Any]:
    target_url = url.strip()
    if not (target_url.startswith("http://") or target_url.startswith("https://")):
        target_url = "https://" + target_url

    try:
        webbrowser.open(target_url)
        logger.info(f"Opened URL in browser: {target_url}")
        return {"status": "success", "message": f"Opened {target_url}."}
    except Exception as e:
        logger.error(f"Failed to open URL '{target_url}': {e}")
        return {"status": "error", "message": f"Could not open URL: {str(e)}"}


@tool_registry.register(
    name="search_web",
    description="Search the web using a search engine like Google or YouTube.",
    parameters={
        "query": {
            "type": "string",
            "description": "Search query keywords (e.g. 'Python async tutorials', 'relaxing music')."
        },
        "engine": {
            "type": "string",
            "description": "Engine to use: 'google' or 'youtube'. Defaults to 'google'.",
            "enum": ["google", "youtube"]
        }
    },
    required=["query"],
    risk_level=0
)
def search_web(query: str, engine: str = "google") -> Dict[str, Any]:
    encoded_query = urllib.parse.quote_plus(query.strip())
    if engine.lower() == "youtube":
        search_url = f"https://www.youtube.com/results?search_query={encoded_query}"
    else:
        search_url = f"https://www.google.com/search?q={encoded_query}"

    try:
        webbrowser.open(search_url)
        logger.info(f"Performed web search ({engine}): {query}")
        return {"status": "success", "message": f"Searching {engine} for '{query}'."}
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"status": "error", "message": f"Search failed: {str(e)}"}
