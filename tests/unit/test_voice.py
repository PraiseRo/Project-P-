import pytest
import pytest_asyncio
from app.voice.speech_to_text import MockSTTProvider, get_stt_provider
from app.voice.text_to_speech import MockTTSProvider, get_tts_provider
from app.voice.microphone import MicrophoneManager

@pytest.mark.asyncio
async def test_mock_stt():
    stt = get_stt_provider("mock")
    text = await stt.transcribe(b"fake_audio_bytes")
    assert text == "open notepad"

@pytest.mark.asyncio
async def test_mock_tts():
    tts = get_tts_provider("mock")
    await tts.speak("Hello world")
    assert "Hello world" in tts.spoken_history

def test_microphone_manager_init():
    mic = MicrophoneManager()
    assert not mic.is_recording
    devices = mic.list_input_devices()
    assert isinstance(devices, list)
