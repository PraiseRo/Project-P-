import asyncio
import threading
import sys
from app.config.settings import get_settings
from app.core.logging_config import setup_logger
from app.core.orchestrator import AssistantOrchestrator
from app.ai.provider import get_ai_provider
from app.voice.speech_to_text import get_stt_provider
from app.voice.text_to_speech import get_tts_provider
from app.voice.microphone import MicrophoneManager
from app.security.policies import SecurityPolicy
from app.ui.overlay import AssistantOverlay

# Import tools package to ensure all default tools are registered
import app.tools

logger = setup_logger("assistant.main")

def main():
    settings = get_settings()
    logger.info("Initializing Project P Voice-Controlled AI Desktop Operator...")

    # 1. Initialize Async Event Loop on a Background Worker Thread
    async_loop = asyncio.new_event_loop()
    def run_async_worker(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    worker_thread = threading.Thread(target=run_async_worker, args=(async_loop,), daemon=True)
    worker_thread.start()

    # 2. Initialize Core Components (Free zero-data Gemini / Web brain support)
    ai_provider = get_ai_provider(
        provider_name=settings.ai_provider,
        api_key=settings.openai_api_key,
        gemini_key=settings.gemini_api_key,
        model=settings.ai_model
    )
    stt_provider = get_stt_provider(
        provider_name=settings.stt_provider,
        api_key=settings.openai_api_key,
        model=settings.stt_model
    )
    tts_provider = get_tts_provider(
        provider_name=settings.tts_provider,
        voice=settings.tts_voice
    )
    microphone_manager = MicrophoneManager(sample_rate=settings.audio_sample_rate)
    security_policy = SecurityPolicy(
        default_permission_level=settings.default_permission_level,
        require_confirmation_for_risky=settings.require_confirmation_for_risky
    )

    # 3. Initialize Master Orchestrator with async_loop
    orchestrator = AssistantOrchestrator(
        ai_provider=ai_provider,
        stt_provider=stt_provider,
        tts_provider=tts_provider,
        microphone_manager=microphone_manager,
        security_policy=security_policy,
        async_loop=async_loop
    )

    # 4. Start Hotkey & Hands-Free Wake-Word Detector ('Hey P')
    orchestrator.hotkey_listener.start()
    orchestrator.wake_detector.start()

    # 5. Text Submission Handler for UI Input
    def on_text_submit(text: str):
        asyncio.run_coroutine_threadsafe(orchestrator.process_text_command(text), async_loop)

    # 6. Launch Desktop UI Overlay HUD (Main GUI Thread)
    app_ui = AssistantOverlay(on_text_submit=on_text_submit)
    logger.info("Project P is live! Speak 'Hey P' hands-free or hold Ctrl+Space.")

    try:
        app_ui.mainloop()
    except KeyboardInterrupt:
        logger.info("Stopping Project P...")
    finally:
        orchestrator.wake_detector.stop()
        orchestrator.hotkey_listener.stop()
        async_loop.call_soon_threadsafe(async_loop.stop)
        logger.info("Project P terminated cleanly.")

if __name__ == "__main__":
    main()
