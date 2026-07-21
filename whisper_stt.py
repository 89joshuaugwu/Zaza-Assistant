"""
Zaza Assistant — Command Transcription (faster-whisper)

Records a voice command with silence-based endpointing and transcribes
it using a local Whisper model. The wake word is handled separately by
wake_word.py (OpenWakeWord) — this module only does command transcription.

First run downloads the Whisper model (~150MB for base.en) from Hugging
Face — needs internet once. After that, fully offline and cached.
"""

import numpy as np
import sounddevice as sd
import time as _time
from faster_whisper import WhisperModel

from config import (
    SAMPLE_RATE, WHISPER_MODEL_SIZE, WHISPER_COMPUTE_TYPE,
    MAX_COMMAND_SECONDS, SILENCE_THRESHOLD, SILENCE_DURATION,
)

_command_model = None


def _get_command_model():
    global _command_model
    if _command_model is None:
        print(f"Loading Whisper command model ({WHISPER_MODEL_SIZE})...")
        _command_model = WhisperModel(
            WHISPER_MODEL_SIZE, device="cpu", compute_type=WHISPER_COMPUTE_TYPE
        )
    return _command_model


_cached_threshold = None
_cached_threshold_time = 0


def _calibrate_silence(duration=0.5):
    """Record a short silence sample and measure the ambient noise floor.
    Returns a threshold slightly above the ambient level so silence
    detection adapts to whatever mic + room combo the user has.

    Caches the result for 60 seconds to avoid recalibrating on every
    command during conversation mode."""
    global _cached_threshold, _cached_threshold_time

    # Reuse cached value if less than 60 seconds old
    if _cached_threshold is not None and (_time.time() - _cached_threshold_time) < 60:
        return _cached_threshold

    try:
        audio = sd.rec(
            int(SAMPLE_RATE * duration), samplerate=SAMPLE_RATE,
            channels=1, dtype="int16"
        )
        sd.wait()
        ambient = np.abs(audio).mean()
        # Set threshold at 3x ambient noise — generous margin above the floor
        threshold = max(int(ambient * 3), 200)  # minimum 200 to avoid over-sensitivity
        print(f"  Ambient noise: {ambient:.0f}, silence threshold set to: {threshold}")
        _cached_threshold = threshold
        _cached_threshold_time = _time.time()
        return threshold
    except Exception:
        return SILENCE_THRESHOLD  # fallback to config value


def _record_until_silence(silence_threshold=None):
    """Records from the mic until you stop talking (or hits the max cap).

    Returns (audio_array, heard_speech). The caller can skip transcription
    if heard_speech is False — this avoids Whisper hallucinations on dead air.
    """
    threshold = silence_threshold or SILENCE_THRESHOLD
    block_duration = 0.2  # seconds per read
    block_size = int(SAMPLE_RATE * block_duration)
    silence_blocks_needed = int(SILENCE_DURATION / block_duration)
    max_blocks = int(MAX_COMMAND_SECONDS / block_duration)

    frames = []
    silent_run = 0
    heard_speech = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        for _ in range(max_blocks):
            data, _ = stream.read(block_size)
            frames.append(data.copy())

            volume = np.abs(data).mean()
            if volume > threshold:
                heard_speech = True
                silent_run = 0
            else:
                silent_run += 1

            if heard_speech and silent_run >= silence_blocks_needed:
                break

    audio = np.concatenate(frames, axis=0).flatten()
    return audio.astype(np.float32) / 32768.0, heard_speech


def listen_for_command():
    """Records a command with silence-based endpointing and transcribes it."""
    # Auto-calibrate silence threshold from current ambient noise
    threshold = _calibrate_silence()

    audio, heard_speech = _record_until_silence(silence_threshold=threshold)

    # Don't waste time transcribing silence — avoids Whisper hallucinations
    if not heard_speech or audio.size < SAMPLE_RATE * 0.3:
        return ""

    model = _get_command_model()
    segments, _ = model.transcribe(audio, language="en", beam_size=5)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    return text
