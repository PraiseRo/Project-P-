import re
import urllib.parse
import httpx
from typing import Dict, Any, List
from app.tools.registry import tool_registry
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.tools.web_research")

def _strip_html(html_text: str) -> str:
    """Quick, dependency-free HTML tag stripper to extract clean body text."""
    # Remove script and style tags completely
    cleaned = re.sub(r'<script.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r'<style.*?</style>', '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    # Remove remaining HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
    # Collapse excess whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

@tool_registry.register(
    name="web_research",
    description="Perform online research on a topic by querying DuckDuckGo/Wikipedia and extracting summary information.",
    parameters={
        "topic": {
            "type": "string",
            "description": "Topic or query to research (e.g. 'Latest NASA discoveries', 'How does quantum computing work', 'Premier league table')."
        }
    },
    required=["topic"],
    risk_level=0
)
async def web_research(topic: str) -> Dict[str, Any]:
    query = topic.strip()
    logger.info(f"Conducting online research for: '{query}'")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers, follow_redirects=True) as client:
            # 1. Try DuckDuckGo Instant Answer API for quick structured facts
            api_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
            resp = await client.get(api_url)
            if resp.status_code == 200:
                data = resp.json()
                abstract = data.get("AbstractText", "")
                if abstract:
                    logger.info("Retrieved summary from Instant Answer API.")
                    return {
                        "status": "success",
                        "topic": query,
                        "source": data.get("AbstractSource", "Web"),
                        "source_url": data.get("AbstractURL", ""),
                        "summary": abstract
                    }

            # 2. Fallback to DuckDuckGo HTML search results extraction
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
            search_resp = await client.get(search_url)
            if search_resp.status_code == 200:
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', search_resp.text, flags=re.DOTALL)
                if snippets:
                    clean_snippets = [_strip_html(s) for s in snippets[:3]]
                    combined = " ".join(clean_snippets)
                    return {
                        "status": "success",
                        "topic": query,
                        "source": "Web Search Snippets",
                        "summary": combined[:1000]
                    }

        return {
            "status": "warning",
            "topic": query,
            "message": "Could not find instant summary online, but web search is available."
        }
    except Exception as e:
        logger.error(f"Web research error for '{query}': {e}")
        return {
            "status": "error",
            "topic": query,
            "message": f"Online research failed: {str(e)}"
        }
