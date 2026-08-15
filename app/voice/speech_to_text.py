import abc
import io
import os
import asyncio
from typing import Optional
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.stt")

class SpeechToTextProvider(abc.ABC):
    """Abstract base class for speech-to-text providers."""

    @abc.abstractmethod
    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = "en") -> str:
        pass


class GeminiMultimodalAudioSTT(SpeechToTextProvider):
    """
    ChatGPT/Gemini-Grade Multimodal Speech Understanding:
    Sends raw audio directly to Gemini 2.5 Flash for human-level acoustic comprehension,
    effortlessly understanding accents, colloquialisms, whispers, and background noise.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Initialized Gemini Multimodal Audio Comprehension Engine.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini GenAI client: {e}")

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = "en") -> str:
        if not audio_bytes:
            return ""

        if not self.client:
            logger.warning("No Gemini API key available, using local free speech recognizer.")
            fallback = FreeSpeechRecognitionSTT()
            return await fallback.transcribe(audio_bytes)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._transcribe_multimodal_sync, audio_bytes)

    def _transcribe_multimodal_sync(self, audio_bytes: bytes) -> str:
        try:
            from google.genai import types
            
            # Send raw audio bytes to Gemini
            part = types.Part.from_bytes(
                data=audio_bytes,
                mime_type="audio/wav"
            )

            prompt = (
                "Listen to this audio clip and transcribe the user's exact spoken words accurately. "
                "Output ONLY the transcribed text without any timestamps, notes, or extra commentary."
            )

            response = self.client.models.generate_content(
                model=self.model,
                contents=[part, prompt]
            )

            transcription = (response.text or "").strip().strip('"').strip("'")
            logger.info(f"Gemini Multimodal transcribed: '{transcription}'")
            return transcription

        except Exception as e:
            logger.warning(f"Gemini Multimodal audio processing error: {e}. Falling back to acoustic engine.")
            fallback = FreeSpeechRecognitionSTT()
            return fallback._transcribe_sync(audio_bytes, "en-US")


class FreeSpeechRecognitionSTT(SpeechToTextProvider):
    """Robust free speech recognizer with automatic ambient noise calibration and multi-attempt retry."""

    def __init__(self):
        import speech_recognition as sr
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 280
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

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
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio_data = self.recognizer.record(source)

            try:
                text = self.recognizer.recognize_google(audio_data, language=language)
                if text:
                    logger.info(f"Transcribed speech: '{text}'")
                    return text
            except sr.UnknownValueError:
                pass

            try:
                text_en = self.recognizer.recognize_google(audio_data, language="en-GB")
                if text_en:
                    logger.info(f"Transcribed speech (accent model): '{text_en}'")
                    return text_en
            except Exception:
                pass

            return ""
        except Exception as e:
            logger.debug(f"STT processing note: {e}")
            return ""


class OpenAIWhisperSTT(SpeechToTextProvider):
    """Cloud-based speech-to-text using the OpenAI Whisper API with automatic fallback."""

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
            logger.debug(f"Whisper fallback to free STT: {e}")
            fallback = FreeSpeechRecognitionSTT()
            return await fallback.transcribe(audio_bytes)


class MockSTTProvider(SpeechToTextProvider):
    """Mock STT provider for offline unit tests and simulation."""
    
    def __init__(self, return_text: str = "open notepad"):
        self.return_text = return_text

    async def transcribe(self, audio_bytes: bytes, language: Optional[str] = "en") -> str:
        return self.return_text


def get_stt_provider(
    provider_name: str,
    api_key: Optional[str] = None,
    gemini_key: Optional[str] = None,
    model: str = "gemini-2.5-flash"
) -> SpeechToTextProvider:
    """Factory function for STT providers with Gemini Multimodal support."""
    normalized = provider_name.lower().strip()
    if gemini_key or normalized in ["gemini", "multimodal", "multimodal_gemini"]:
        return GeminiMultimodalAudioSTT(api_key=gemini_key or api_key, model=model)
    elif normalized in ["openai", "openai_whisper", "whisper"]:
        if api_key:
            return OpenAIWhisperSTT(api_key=api_key, model=model)
        return GeminiMultimodalAudioSTT(api_key=gemini_key)
    elif normalized == "mock":
        return MockSTTProvider()
    else:
        if gemini_key:
            return GeminiMultimodalAudioSTT(api_key=gemini_key, model=model)
        return FreeSpeechRecognitionSTT()
