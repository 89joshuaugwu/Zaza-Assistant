"""
Zaza Assistant — Text to Speech (offline, via pyttsx3)
"""

import pyttsx3
from config import TTS_RATE, TTS_VOLUME

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", TTS_RATE)
        _engine.setProperty("volume", TTS_VOLUME)
    return _engine


def speak(text: str):
    if not text:
        return
    print(f"Zaza: {text}")
    engine = _get_engine()
    engine.say(text)
    engine.runAndWait()
