import abc
import json
from typing import List, Dict, Any, Optional
from app.core.logging_config import setup_logger
from app.tools.registry import tool_registry

logger = setup_logger("assistant.ai")

SYSTEM_PROMPT = """You are an intelligent, helpful voice-controlled Windows PC Desktop Assistant.
Your job is to assist the user by executing tasks on their computer, answering questions, or launching applications.

Rules:
1. When the user asks you to perform a PC task (such as opening an application, searching YouTube, creating a folder or file, checking system stats), select and call the appropriate tool.
2. If the user asks a general knowledge question or conversation, answer clearly, politely, and concisely so it sounds great when spoken aloud via Text-to-Speech.
3. Keep spoken voice responses concise and natural (avoid excessively long outputs unless specifically requested).
4. Never assume a destructive action succeeded without calling the proper tool.
"""

class AIProvider(abc.ABC):
    """Abstract base class for AI LLM providers."""

    @abc.abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Generates a response from the LLM given conversation history and available tools."""
        pass


class OpenAIProvider(AIProvider):
    """OpenAI API Provider with native tool calling."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        try:
            response = await self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            
            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": json.loads(tc.function.arguments)
                    })

            return {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": tool_calls
            }
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}", exc_info=True)
            raise


class MockAIProvider(AIProvider):
    """Mock AI Provider for tests and offline simulation."""

    def __init__(self, response_text: str = "I am ready.", mock_tool_call: Optional[Dict[str, Any]] = None):
        self.response_text = response_text
        self.mock_tool_call = mock_tool_call

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        tool_calls = [self.mock_tool_call] if self.mock_tool_call else []
        return {
            "role": "assistant",
            "content": self.response_text,
            "tool_calls": tool_calls
        }


def get_ai_provider(provider_name: str, api_key: Optional[str] = None, model: str = "gpt-4o-mini") -> AIProvider:
    norm = provider_name.lower().strip()
    if norm in ["openai", "gpt"]:
        return OpenAIProvider(api_key=api_key, model=model)
    elif norm == "mock":
        return MockAIProvider()
    else:
        logger.warning(f"Unknown provider '{provider_name}', defaulting to OpenAI.")
        return OpenAIProvider(api_key=api_key, model=model)
