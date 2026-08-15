import abc
import io
import asyncio
from typing import Optional
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.stt")

class SpeechToTextProvider(abc.ABC):
    """Abstract base class for speech-to-text providers."""

    @abc.abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = "en") -> str:
        """Converts WAV audio bytes to transcribed text string."""
        pass


class FreeSpeechRecognitionSTT(SpeechToTextProvider):
    """Free built-in speech recognizer (zero API key needed)."""

    def __init__(self):
        import speech_recognition as sr
        self.recognizer = sr.Recognizer()

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = "en-US") -> str:
        if not audio_bytes:
            return ""
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._transcribe_sync, audio_bytes, language)

    def _transcribe_sync(self, audio_bytes: bytes, language: str) -> str:
        import speech_recognition as sr
        try:
            audio_file = io.BytesIO(audio_bytes)
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
            text = self.recognizer.recognize_google(audio_data, language=language)
            logger.info(f"Transcribed speech: '{text}'")
            return text
        except sr.UnknownValueError:
            logger.warning("Speech recognition could not understand audio.")
            return ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected STT error: {e}")
            return ""


class OpenAIWhisperSTT(SpeechToTextProvider):
    """Cloud-based speech-to-text using the OpenAI Whisper API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        if api_key:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
        else:
            self.client = None
        self.model = model

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = "en") -> str:
        if not audio_bytes:
            return ""
        
        if not self.client:
            logger.warning("No OpenAI API key provided, falling back to Free Speech Recognizer.")
            fallback = FreeSpeechRecognitionSTT()
            return await fallback.transcribe(audio_bytes)

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "input_audio.wav"

            kwargs = {
                "file": audio_file,
                "model": self.model,
            }
            if language:
                kwargs["language"] = language

            response = await self.client.audio.transcriptions.create(**kwargs)
            transcription = response.text.strip()
            logger.info(f"OpenAI Whisper transcribed: '{transcription}'")
            return transcription
        except Exception as e:
            logger.error(f"OpenAI Whisper transcription failed: {e}", exc_info=True)
            fallback = FreeSpeechRecognitionSTT()
            return await fallback.transcribe(audio_bytes)


class MockSTTProvider(SpeechToTextProvider):
    """Mock STT provider for offline unit tests and simulation."""
    
    def __init__(self, return_text: str = "open notepad"):
        self.return_text = return_text

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = "en") -> str:
        return self.return_text


def get_stt_provider(provider_name: str, api_key: Optional[str] = None, model: str = "whisper-1") -> SpeechToTextProvider:
    """Factory function for STT providers."""
    normalized = provider_name.lower().strip()
    if normalized in ["openai", "openai_whisper", "whisper"]:
        if api_key:
            return OpenAIWhisperSTT(api_key=api_key, model=model)
        return FreeSpeechRecognitionSTT()
    elif normalized in ["free", "default", "google", "speech_recognition"]:
        return FreeSpeechRecognitionSTT()
    elif normalized == "mock":
        return MockSTTProvider()
    else:
        return FreeSpeechRecognitionSTT()
