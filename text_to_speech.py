"""
Zaza Assistant — Text to Speech (offline, via pyttsx3)
"""

import pyttsx3
from config import TTS_RATE, TTS_VOLUME, TTS_VOICE_INDEX, ASSISTANT_NAME

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", TTS_RATE)
        _engine.setProperty("volume", TTS_VOLUME)
        # Select voice by index (0 = default, 1 = alternate, etc.)
        voices = _engine.getProperty("voices")
        if voices and TTS_VOICE_INDEX < len(voices):
            _engine.setProperty("voice", voices[TTS_VOICE_INDEX].id)
    return _engine


def speak(text: str):
    if not text:
        return
    print(f"{ASSISTANT_NAME}: {text}")
    engine = _get_engine()
    engine.say(text)
    engine.runAndWait()
