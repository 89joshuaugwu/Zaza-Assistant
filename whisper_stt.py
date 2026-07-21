"""
Zaza Assistant — Speech Recognition (faster-whisper)

Handles BOTH:
  1. listen_for_wake_word() — polls short chunks with a fast/tiny Whisper
     model, checking each for WAKE_WORD. More accurate than Vosk on
     non-dictionary words like "zaza", at the cost of higher CPU/battery
     use since it's actively transcribing while idle (not just listening).
  2. listen_for_command()   — records with silence-based endpointing and
     transcribes with a larger/more accurate Whisper model.

First run downloads both models from Hugging Face (~40MB tiny.en + ~150MB
base.en) — needs internet once. After that, fully offline and cached.
"""

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import (
    SAMPLE_RATE, WAKE_WORD, WAKE_WHISPER_MODEL_SIZE, WAKE_POLL_SECONDS,
    WHISPER_MODEL_SIZE, WHISPER_COMPUTE_TYPE,
    MAX_COMMAND_SECONDS, SILENCE_THRESHOLD, SILENCE_DURATION,
)

_command_model = None
_wake_model = None


def _get_command_model() -> WhisperModel:
    global _command_model
    if _command_model is None:
        print(f"Loading Whisper command model ({WHISPER_MODEL_SIZE})...")
        _command_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type=WHISPER_COMPUTE_TYPE)
    return _command_model


def _get_wake_model() -> WhisperModel:
    global _wake_model
    if _wake_model is None:
        print(f"Loading Whisper wake-word model ({WAKE_WHISPER_MODEL_SIZE})...")
        _wake_model = WhisperModel(WAKE_WHISPER_MODEL_SIZE, device="cpu", compute_type=WHISPER_COMPUTE_TYPE)
    return _wake_model


def _record_fixed(seconds: float) -> np.ndarray:
    """Blocking fixed-length recording — used for wake-word polling."""
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    return audio.flatten().astype(np.float32) / 32768.0


def listen_for_wake_word():
    """Blocks until WAKE_WORD is heard in a polled audio chunk."""
    model = _get_wake_model()
    print(f"Listening for wake word: '{WAKE_WORD}'...")
    while True:
        audio = _record_fixed(WAKE_POLL_SECONDS)
        segments, _ = model.transcribe(audio, language="en", beam_size=1)
        text = " ".join(seg.text.strip() for seg in segments).lower()
        if WAKE_WORD in text:
            return


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

    model = _get_command_model()
    segments, _ = model.transcribe(audio, language="en", beam_size=5)
    text = " ".join(seg.text.strip() for seg in segments).strip()
    return text
