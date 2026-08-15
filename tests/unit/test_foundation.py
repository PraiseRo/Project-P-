from app.config.settings import Settings, get_settings
from app.core.logging_config import setup_logger
from app.core.events import AssistantState, event_bus
import logging

def test_settings_defaults():
    settings = get_settings()
    assert settings.ai_provider in ["hybrid", "openai", "gemini", "ollama"]
    assert settings.push_to_talk_key == "ctrl+space"
    assert settings.emergency_stop_key == "ctrl+alt+esc"
    assert settings.default_permission_level == 1

def test_secret_redaction(capsys):
    logger = setup_logger("test_logger", logging.INFO)
    logger.info("Connecting with key sk-1234567890abcdef1234567890abcdef")
    captured = capsys.readouterr()
    assert "sk-1234567890abcdef1234567890abcdef" not in captured.out
    assert "***REDACTED_SECRET***" in captured.out

def test_event_bus():
    received = []
    def on_state_change(state):
        received.append(state)

    event_bus.subscribe("state_change", on_state_change)
    event_bus.publish("state_change", AssistantState.LISTENING)
    assert received == [AssistantState.LISTENING]
