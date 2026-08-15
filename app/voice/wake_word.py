import io
import time
import wave
import threading
import numpy as np
import sounddevice as sd
from typing import Callable, Optional, List
from app.voice.speech_to_text import SpeechToTextProvider
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.wake_word")

WAKE_PHRASES = ["hey p", "project p", "hello p", "hi p", "hey computer", "hey assistant"]

class WakeWordDetector:
    """
    Low-CPU background streaming listener that monitors microphone audio,
    detects wake phrases ('Hey P'), and captures commands with Voice Activity Detection (VAD).
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

        # VAD & Energy thresholds
        self.energy_threshold = 400
        self.silence_limit_seconds = 1.2
        self.state = "WAKE_WORD_LISTENING"  # "WAKE_WORD_LISTENING" or "COMMAND_LISTENING"
        self._command_frames: List[np.ndarray] = []

    def start(self):
        """Starts background hands-free listening thread."""
        if not self.is_running:
            self.is_running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            logger.info("Hands-free Wake-Word listening active ('Hey P').")

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

                    # Calculate audio root-mean-square energy
                    energy = np.sqrt(np.mean(data.astype(np.float32) ** 2))

                    if self.state == "WAKE_WORD_LISTENING":
                        # Only process if user is actively speaking above background ambient noise
                        if energy > self.energy_threshold:
                            rolling_buffer.append(data.copy())
                            if len(rolling_buffer) > 4:  # ~2 seconds window
                                rolling_buffer.pop(0)

                            # Check rolling audio for wake word
                            if len(rolling_buffer) >= 2:
                                audio_bytes = self._encode_wav(np.concatenate(rolling_buffer))
                                # Run quick async transcription check
                                transcribed = self._transcribe_sync(audio_bytes).lower()
                                
                                if any(phrase in transcribed for phrase in WAKE_PHRASES):
                                    logger.info(f"Wake word detected in: '{transcribed}'")
                                    rolling_buffer.clear()
                                    self.state = "COMMAND_LISTENING"
                                    self._command_frames = []
                                    # Trigger instant visual/audio feedback
                                    self.on_wake_word_detected()
                        else:
                            if rolling_buffer:
                                rolling_buffer.pop(0)

                    elif self.state == "COMMAND_LISTENING":
                        # In command listening mode: accumulate frames until silence is detected
                        self._command_frames.append(data.copy())

                        # Check for silence or max duration (10s)
                        if len(self._command_frames) > 20: # 10 seconds timeout
                            self._finalize_command()
                        elif len(self._command_frames) >= 4 and energy < self.energy_threshold:
                            # 2 blocks of silence (1s) after speaking
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
