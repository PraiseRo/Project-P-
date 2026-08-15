import abc
import os
import io
import asyncio
import tempfile
import threading
from typing import Optional
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.tts")

class TextToSpeechProvider(abc.ABC):
    """Abstract base class for Text-to-Speech synthesis."""

    @abc.abstractmethod
    async def speak(self, text: str) -> None:
        """Synthesizes and plays the provided text aloud."""
        pass


class NativePyttsx3Provider(TextToSpeechProvider):
    """Pre-warmed, zero-latency Windows SAPI5 TTS engine."""

    def __init__(self, voice_id: Optional[str] = None):
        self.voice_id = voice_id
        self._lock = threading.Lock()

    async def speak(self, text: str) -> None:
        if not text or not text.strip():
            return
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._speak_sync, text)

    def _speak_sync(self, text: str):
        with self._lock:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 185)  # Slightly faster, punchy conversational speed
                if self.voice_id:
                    engine.setProperty('voice', self.voice_id)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"pyttsx3 speech failed: {e}", exc_info=True)


class EdgeTTSProvider(TextToSpeechProvider):
    """High quality neural text-to-speech with pre-allocated buffer."""

    def __init__(self, voice: str = "en-US-ChristopherNeural", rate: str = "+10%", volume: str = "+0%"):
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def speak(self, text: str) -> None:
        if not text or not text.strip():
            return
        
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text=text, voice=self.voice, rate=self.rate, volume=self.volume)
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_filename = f.name

            try:
                await communicate.save(temp_filename)
                
                proc = await asyncio.create_subprocess_shell(
                    f'powershell -c "(New-Object Media.SoundPlayer \'{temp_filename}\').PlaySync()"',
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await proc.wait()
            finally:
                if os.path.exists(temp_filename):
                    try:
                        os.remove(temp_filename)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"EdgeTTS unavailable, falling back to instant Native SAPI5: {e}")
            fallback = NativePyttsx3Provider()
            await fallback.speak(text)


class MockTTSProvider(TextToSpeechProvider):
    """Mock TTS for unit tests and headless environments."""
    
    def __init__(self):
        self.spoken_history = []

    async def speak(self, text: str) -> None:
        logger.info(f"[MockTTS] Spoke: '{text}'")
        self.spoken_history.append(text)


def get_tts_provider(provider_name: str, voice: str = "en-US-ChristopherNeural") -> TextToSpeechProvider:
    normalized = provider_name.lower().strip()
    if normalized in ["edge_tts", "edge"]:
        return EdgeTTSProvider(voice=voice)
    elif normalized in ["pyttsx3", "native", "offline", "fast", "turbo"]:
        return NativePyttsx3Provider()
    elif normalized == "mock":
        return MockTTSProvider()
    else:
        return EdgeTTSProvider(voice=voice)
