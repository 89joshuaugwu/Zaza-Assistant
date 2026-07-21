"""
Zaza Assistant — Wake Word Detection (offline, via Vosk)
Only handles listen_for_wake_word() — blocks until the wake phrase is heard.
Actual command transcription happens in whisper_stt.py instead, since Vosk's
small model was too inaccurate for full sentences.
"""

import json
import queue
import os

import sounddevice as sd
from vosk import Model, KaldiRecognizer

from config import VOSK_MODEL_PATH, SAMPLE_RATE, WAKE_WORD

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

