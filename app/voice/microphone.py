import io
import wave
import numpy as np
import sounddevice as sd
from typing import List, Dict, Any, Optional
from app.core.logging_config import setup_logger

logger = setup_logger("assistant.microphone")

class MicrophoneManager:
    """Manages audio recording devices, recording streams, volume boost, and audio buffer generation."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.selected_device_index: Optional[int] = None
        self._is_recording = False
        self._recorded_frames: List[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None

    def list_input_devices(self) -> List[Dict[str, Any]]:
        """Returns all available audio input devices."""
        devices = []
        try:
            for idx, dev in enumerate(sd.query_devices()):
                if dev.get('max_input_channels', 0) > 0:
                    devices.append({
                        "id": idx,
                        "name": dev.get('name'),
                        "hostapi": dev.get('hostapi'),
                        "channels": dev.get('max_input_channels'),
                        "default_samplerate": dev.get('default_samplerate')
                    })
        except Exception as e:
            logger.error(f"Failed to query audio devices: {e}")
        return devices

    def set_device(self, device_id: int):
        """Sets the active input microphone device ID."""
        self.selected_device_index = device_id
        logger.info(f"Microphone set to device index: {device_id}")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio stream status issue: {status}")
        if self._is_recording:
            self._recorded_frames.append(indata.copy())

    def start_recording(self):
        """Starts capturing audio frames into memory."""
        if self._is_recording:
            return
        
        self._recorded_frames = []
        self._is_recording = True
        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                device=self.selected_device_index,
                callback=self._audio_callback
            )
            self._stream.start()
            logger.info("Microphone recording started.")
        except Exception as e:
            self._is_recording = False
            logger.error(f"Failed to start audio stream: {e}", exc_info=True)
            raise

    def stop_recording(self) -> bytes:
        """Stops capturing audio, applies Automatic Gain Control (AGC) for low voices, and returns a WAV buffer."""
        if not self._is_recording:
            return b""
        
        self._is_recording = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
            self._stream = None

        if not self._recorded_frames:
            logger.warning("No audio frames were captured.")
            return b""

        # Concatenate audio data into a single continuous numpy array
        audio_data = np.concatenate(self._recorded_frames, axis=0)

        # Automatic Gain Control (AGC) & Volume Normalization for low / quiet voices
        audio_float = audio_data.astype(np.float32)
        max_amplitude = np.max(np.abs(audio_float))
        
        if max_amplitude > 0:
            target_peak = 26000.0  # Max 16-bit is ~32767
            gain = min(target_peak / max_amplitude, 6.0) # Up to 6x amplification for quiet voices
            if gain > 1.2:
                logger.info(f"Boosting low-volume voice by {gain:.2f}x gain factor.")
                audio_float = audio_float * gain
                audio_data = np.clip(audio_float, -32767, 32767).astype(np.int16)
        
        # Write to in-memory WAV buffer
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit PCM = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())

        wav_bytes = wav_buffer.getvalue()
        logger.info(f"Recording stopped. Processed audio bytes: {len(wav_bytes)}")
        return wav_bytes

    @property
    def is_recording(self) -> bool:
        return self._is_recording
