"""
Zaza Assistant — Speech to Text (offline, via Vosk)
Two modes:
  1. listen_for_wake_word() — blocks until the wake phrase is heard
  2. listen_for_command()   — records a few seconds and transcribes it
"""

import json
import queue
import os

import sounddevice as sd
from vosk import Model, KaldiRecognizer

from config import VOSK_MODEL_PATH, SAMPLE_RATE, WAKE_WORD, COMMAND_LISTEN_SECONDS

_audio_q = queue.Queue()


def _callback(indata, frames, time, status):
    _audio_q.put(bytes(indata))


def _load_model() -> Model:
    if not os.path.isdir(VOSK_MODEL_PATH):
        raise FileNotFoundError(
            f"Vosk model not found at {VOSK_MODEL_PATH}.\n"
            "Download it — see README.md step 3."
        )
    return Model(VOSK_MODEL_PATH)


_model = None


def _get_model():
    global _model
    if _model is None:
        _model = _load_model()
    return _model


def listen_for_wake_word():
    """Blocks the thread until WAKE_WORD is heard in the mic stream."""
    rec = KaldiRecognizer(_get_model(), SAMPLE_RATE)
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16",
        channels=1, callback=_callback
    ):
        print(f"Listening for wake word: '{WAKE_WORD}'...")
        while True:
            data = _audio_q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower()
                if WAKE_WORD in text:
                    return


def listen_for_command(seconds: int = COMMAND_LISTEN_SECONDS) -> str:
    """Records `seconds` of audio and returns the transcribed text."""
    rec = KaldiRecognizer(_get_model(), SAMPLE_RATE)
    frames_needed = int(SAMPLE_RATE * seconds / 8000)

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16",
        channels=1, callback=_callback
    ):
        print("Listening for your command...")
        # drain any leftover audio from the wake-word phase
        while not _audio_q.empty():
            _audio_q.get()

        for _ in range(frames_needed):
            data = _audio_q.get()
            rec.AcceptWaveform(data)

        final = json.loads(rec.FinalResult())
        return final.get("text", "").strip()
