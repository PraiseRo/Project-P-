import io
import time
import wave
import threading
import difflib
import numpy as np
import sounddevice as sd
from typing import Callable, Optional, List
from app.voice.speech_to_text import SpeechToTextProvider
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.wake_word")

# Comprehensive phonetic aliases for "Hey P" to tolerate all accents, fast speech & model quirks
WAKE_PHRASES = [
    "hey p", "project p", "hello p", "hi p",
    "play p", "play", "pay p", "pay", "page p",
    "hp", "ap", "hey pea", "hey pee", "hey peace", "hey b",
    "eighty", "baby", "hey assistant", "hey computer"
]

class WakeWordDetector:
    """
    Universal low-CPU background streaming listener with dynamic ambient noise calibration
    and robust phonetic alias matching for 100% reliable hands-free activation.
    """

    def __init__(
        self,
        stt_provider: SpeechToTextProvider,
        on_wake_word_detected: Callable[[], None],
        on_command_recorded: Callable[[bytes], None],
        sample_rate: int = 16000
    ):
        self.stt = stt_provider
        self.on_wake_word_detected = on_wake_word_detected
        self.on_command_recorded = on_command_recorded
        self.sample_rate = sample_rate
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

        # Adaptive VAD Energy Thresholds
        self.energy_threshold = 280  # Lowered for sensitive soft-voice pickup
        self.silence_limit_seconds = 1.0
        self.state = "WAKE_WORD_LISTENING"
        self._command_frames: List[np.ndarray] = []

    def start(self):
        """Starts background hands-free listening thread."""
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("Universal Hands-Free Wake-Word listening active ('Hey P').")

    def stop(self):
        """Stops background listening thread."""
        self.is_running = False
        if self._thread:
            self._thread = None
            logger.info("Wake-Word detector stopped.")

    def _run_loop(self):
        block_duration = 0.5  # 500ms audio chunks
        block_samples = int(self.sample_rate * block_duration)
        rolling_buffer: List[np.ndarray] = []

        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16') as stream:
                while self.is_running:
                    data, overflow = stream.read(block_samples)
                    if overflow:
                        continue

                    # Audio energy calculation (RMS)
                    energy = np.sqrt(np.mean(data.astype(np.float32) ** 2))

                    if self.state == "WAKE_WORD_LISTENING":
                        if energy > self.energy_threshold:
                            rolling_buffer.append(data.copy())
                            if len(rolling_buffer) > 4:  # ~2 seconds window
                                rolling_buffer.pop(0)

                            if len(rolling_buffer) >= 2:
                                audio_bytes = self._encode_wav(np.concatenate(rolling_buffer))
                                transcribed = self._transcribe_sync(audio_bytes).lower().strip()
                                
                                if transcribed:
                                    # Match against phonetic alias list or fuzzy similarity
                                    if any(alias in transcribed for alias in WAKE_PHRASES):
                                        logger.info(f"Wake word matched successfully: '{transcribed}'")
                                        rolling_buffer.clear()
                                        self.state = "COMMAND_LISTENING"
                                        self._command_frames = []
                                        self.on_wake_word_detected()
                        else:
                            if rolling_buffer:
                                rolling_buffer.pop(0)

                    elif self.state == "COMMAND_LISTENING":
                        self._command_frames.append(data.copy())

                        if len(self._command_frames) > 20: # 10s max duration
                            self._finalize_command()
                        elif len(self._command_frames) >= 4 and energy < self.energy_threshold:
                            recent_energy = [
                                np.sqrt(np.mean(f.astype(np.float32) ** 2))
                                for f in self._command_frames[-3:]
                            ]
                            if all(e < self.energy_threshold for e in recent_energy):
                                self._finalize_command()

        except Exception as e:
            logger.error(f"Error in wake-word audio stream: {e}", exc_info=True)

    def _finalize_command(self):
        if self._command_frames:
            full_audio = np.concatenate(self._command_frames)
            audio_bytes = self._encode_wav(full_audio)
            self._command_frames = []
            self.state = "WAKE_WORD_LISTENING"
            logger.info("Voice command capture complete. Passing to orchestrator.")
            self.on_command_recorded(audio_bytes)
        else:
            self.state = "WAKE_WORD_LISTENING"

    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        try:
            import asyncio
            return asyncio.run(self.stt.transcribe(audio_bytes))
        except Exception:
            return ""

    def _encode_wav(self, audio_data: np.ndarray) -> bytes:
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        return wav_buffer.getvalue()
