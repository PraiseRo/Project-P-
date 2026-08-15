import pytest
import pytest_asyncio
from app.ai.provider import MockAIProvider
from app.voice.speech_to_text import MockSTTProvider
from app.voice.text_to_speech import MockTTSProvider
from app.core.orchestrator import AssistantOrchestrator
from app.core.events import AssistantState

@pytest.mark.asyncio
async def test_orchestrator_general_chat():
    ai = MockAIProvider(response_text="Hello! How can I help you today?")
    stt = MockSTTProvider(return_text="Hello assistant")
    tts = MockTTSProvider()
    
    orchestrator = AssistantOrchestrator(ai_provider=ai, stt_provider=stt, tts_provider=tts)
    await orchestrator.process_text_command("Hello assistant")
    
    assert orchestrator.state == AssistantState.IDLE
    assert "Hello! How can I help you today?" in tts.spoken_history

@pytest.mark.asyncio
async def test_orchestrator_tool_execution():
    tool_call = {
        "id": "call_test_1",
        "name": "get_system_info",
        "arguments": {}
    }
    ai = MockAIProvider(response_text="Here is your system status.", mock_tool_call=tool_call)
    stt = MockSTTProvider(return_text="What is my CPU usage?")
    tts = MockTTSProvider()
    
    orchestrator = AssistantOrchestrator(ai_provider=ai, stt_provider=stt, tts_provider=tts)
    await orchestrator.process_text_command("What is my CPU usage?")
    
    assert orchestrator.state == AssistantState.IDLE
    assert len(tts.spoken_history) > 0
