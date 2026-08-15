import abc
import json
import os
import re
from typing import List, Dict, Any, Optional
from app.core.logging_config import setup_logger
from app.tools.registry import tool_registry

logger = setup_logger("assistant.ai")

SYSTEM_PROMPT = """You are Project P, an articulate, witty, and highly intelligent voice AI assistant built by Praise.
Your voice is spoken directly into the user's ears via Text-to-Speech.

Rules:
1. When asked to debate, discuss research, or answer questions:
   - Provide articulate, well-reasoned, and engaging conversational answers.
   - Keep spoken replies concise and punchy (1 to 3 paragraphs max) unless asked to elaborate.
   - Speak naturally without bullet lists, markdown asterisks, or formatting that sounds awkward when read aloud.
2. When the user asks for PC tasks (opening apps, files, routines, system info), trigger the appropriate tool.
3. Be friendly, sharp, and address the user by name (Praise) occasionally.
"""

class AIProvider(abc.ABC):
    """Abstract base class for AI LLM providers."""

    @abc.abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        pass


class GeminiProvider(AIProvider):
    """
    Google Gemini Provider: 100% Free tier (zero download, GPT-4 grade intelligence)
    Ideal for deep research discussions, debates, and Q&A.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI client: {e}")

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not set. Set GEMINI_API_KEY in .env for free unlimited debate and research.")

        try:
            # Format history for Gemini
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    prompt_parts.append(f"{role.upper()}: {content}")

            combined_prompt = "\n".join(prompt_parts) + "\nASSISTANT:"

            response = self.client.models.generate_content(
                model=self.model,
                contents=combined_prompt
            )

            text_resp = response.text or ""
            # Strip markdown formatting like asterisks for cleaner speech synthesis
            cleaned_text = re.sub(r'[*_#`]', '', text_resp).strip()

            return {
                "role": "assistant",
                "content": cleaned_text,
                "tool_calls": []
            }
        except Exception as e:
            logger.error(f"Gemini generation error: {e}", exc_info=True)
            raise


class OpenAIProvider(AIProvider):
    """OpenAI API Provider with native tool calling."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key) if api_key else None
        self.model = model

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        if not self.client:
            raise ValueError("OPENAI_API_KEY is not configured.")

        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

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


class HybridKnowledgeProvider(AIProvider):
    """
    Zero-download conversational provider that uses live Web research & facts
    when no cloud API key is supplied.
    """

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        last_user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user_msg = m.get("content", "")
                break

        # Check if user wants research or facts
        from app.tools.web_research import web_research
        research_result = await web_research(last_user_msg)
        if research_result.get("status") == "success":
            summary = research_result.get("summary", "")
            return {
                "role": "assistant",
                "content": f"According to online research: {summary}",
                "tool_calls": []
            }

        return {
            "role": "assistant",
            "content": f"I heard your question about '{last_user_msg}'. You can connect a free Gemini API key in your .env file for deep debates, or use local PC commands.",
            "tool_calls": []
        }


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


def get_ai_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    gemini_key: Optional[str] = None,
    model: str = "gemini-2.5-flash"
) -> AIProvider:
    norm = provider_name.lower().strip()
    if norm in ["gemini", "google", "free_gemini"]:
        return GeminiProvider(api_key=gemini_key, model=model)
    elif norm in ["openai", "gpt"]:
        return OpenAIProvider(api_key=api_key)
    elif norm == "mock":
        return MockAIProvider()
    elif gemini_key:
        return GeminiProvider(api_key=gemini_key)
    elif api_key:
        return OpenAIProvider(api_key=api_key)
    else:
        return HybridKnowledgeProvider()
