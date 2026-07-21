"""
Zaza Assistant — Text to Speech (offline, via pyttsx3)
"""

import pyttsx3
import threading
import queue
from config import TTS_RATE, TTS_VOLUME, TTS_VOICE_INDEX, ASSISTANT_NAME

_tts_queue = queue.Queue()

def _tts_worker():
    # Initialize COM for background thread (required for Windows SAPI5)
    import pythoncom
    pythoncom.CoInitialize()
    
    while True:
        text = _tts_queue.get()
        if text is None:
            break
        try:
            # Re-initialize engine per sentence to prevent SAPI5 state corruption
            engine = pyttsx3.init()
            engine.setProperty("rate", TTS_RATE)
            engine.setProperty("volume", TTS_VOLUME)
            # Select voice by index (0 = default, 1 = alternate, etc.)
            voices = engine.getProperty("voices")
            if voices and TTS_VOICE_INDEX < len(voices):
                engine.setProperty("voice", voices[TTS_VOICE_INDEX].id)
                
            engine.say(text)
            engine.runAndWait()
            del engine  # Free COM resources
        except Exception as e:
            print(f"\n[TTS Error: {e}]\n")
        finally:
            _tts_queue.task_done()

# Start the background worker thread
threading.Thread(target=_tts_worker, daemon=True).start()

def speak(text: str, print_out: bool = True):
    if not text:
        return
    if print_out:
        print(f"{ASSISTANT_NAME}: {text}")
    _tts_queue.put(text)

def wait_until_done():
    """Blocks until all queued text has been spoken."""
    _tts_queue.join()
