"""
Zaza Assistant — Command Transcription (faster-whisper)

Vosk (speech_to_text.py) handles the wake word — fast, low overhead, "good
enough" for spotting one keyword. This module handles the actual command —
much higher accuracy for general speech, which is what was garbling things
like "what is today's date" into nonsense.

First run downloads the model (~150MB for base.en) from Hugging Face — needs
internet once. After that it's cached locally and runs fully offline.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import (
    SAMPLE_RATE, WHISPER_MODEL_SIZE, WHISPER_COMPUTE_TYPE,
    MAX_COMMAND_SECONDS, SILENCE_THRESHOLD, SILENCE_DURATION,
)

_model = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        print(f"Loading Whisper model ({WHISPER_MODEL_SIZE})...")
        _model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type=WHISPER_COMPUTE_TYPE)
    return _model


def _record_until_silence() -> np.ndarray:
    """Records from the mic until you stop talking (or hits the max cap).
    This replaces a fixed-duration recording so it doesn't cut you off mid
    sentence or sit there recording dead air after you're done."""
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
            if volume > SILENCE_THRESHOLD:
                heard_speech = True
                silent_run = 0
            else:
                silent_run += 1

            if heard_speech and silent_run >= silence_blocks_needed:
                break

    audio = np.concatenate(frames, axis=0).flatten()
    return audio.astype(np.float32) / 32768.0  # int16 -> normalized float32 for whisper


def listen_for_command() -> str:
    """Records a command with silence-based endpointing and transcribes it."""
    audio = _record_until_silence()
    if audio.size < SAMPLE_RATE * 0.3:  # essentially nothing recorded
        return ""

    model = _get_model()
    segments, _ = model.transcribe(audio, language="en", beam_size=5)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    return text
