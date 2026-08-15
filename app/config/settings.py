import re
import logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # AI Configuration
    ai_provider: str = Field(default="openai", description="AI Provider: openai, gemini, or ollama")
    ai_model: str = Field(default="gpt-4o-mini", description="Model name to use")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API Key")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama server endpoint")

    # Speech-to-Text (STT) Configuration
    stt_provider: str = Field(default="openai_whisper", description="STT Provider: openai_whisper or faster_whisper")
    stt_model: str = Field(default="whisper-1", description="STT model identifier")
    stt_language: str = Field(default="en", description="Default transcription language")

    # Text-to-Speech (TTS) Configuration
    tts_provider: str = Field(default="edge_tts", description="TTS Provider: edge_tts or pyttsx3")
    tts_voice: str = Field(default="en-US-ChristopherNeural", description="Voice profile identifier")
    tts_rate: str = Field(default="0%", description="Speaking rate modification")
    tts_volume: str = Field(default="100%", description="Speaking volume modification")

    # Voice & Hotkey Settings
    push_to_talk_key: str = Field(default="ctrl+space", description="Global push-to-talk hotkey")
    emergency_stop_key: str = Field(default="ctrl+alt+esc", description="Global emergency abort hotkey")
    audio_sample_rate: int = Field(default=16000, description="Audio recording sample rate")
    silence_timeout_seconds: float = Field(default=1.5, description="Silence duration to stop recording")
    max_recording_seconds: float = Field(default=30.0, description="Maximum voice clip length")

    # Security & Execution Policies
    default_permission_level: int = Field(default=1, description="Default permission level (0=Safe, 1=Low, 2=Moderate, 3=High)")
    require_confirmation_for_risky: bool = Field(default=True, description="Enforce voice/UI confirmation for Level 2 and 3 actions")

    # UI Settings
    minimize_to_tray: bool = Field(default=True, description="Minimize application to Windows system tray")
    dark_mode: bool = Field(default=True, description="Use dark mode theme")


def get_settings() -> Settings:
    return Settings()
