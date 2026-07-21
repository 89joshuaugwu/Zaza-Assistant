"""
Zaza Assistant — Wake Word Detection (OpenWakeWord)

Purpose-built neural wake word engine that streams audio continuously
from the microphone and detects the configured wake word with high
accuracy and very low CPU usage (~1-3%).

First run downloads the pre-trained model (~few MB) — needs internet
once. After that, fully offline and cached.
"""

import numpy as np
import sounddevice as sd

from config import SAMPLE_RATE, WAKE_MODEL, WAKE_THRESHOLD, ASSISTANT_NAME

_model = None


def _get_model():
    """Lazy-load the OpenWakeWord model (downloads on first run)."""
    global _model
    if _model is None:
        print(f"Loading wake word model ({WAKE_MODEL})...")
        try:
            import openwakeword
            openwakeword.utils.download_models()
            from openwakeword.model import Model
            _model = Model(wakeword_models=[WAKE_MODEL])
        except Exception as e:
            raise RuntimeError(
                f"Failed to load OpenWakeWord model '{WAKE_MODEL}': {e}\n"
                "Make sure openwakeword is installed: pip install openwakeword\n"
                "First run needs internet to download the model (~few MB)."
            ) from e
    return _model


def listen_for_wake_word():
    """Blocks until the wake word is heard in the continuous mic stream.

    Uses OpenWakeWord — a purpose-built wake word engine that processes
    80ms audio chunks in a tight loop with no gaps. Much more accurate
    and much lighter on CPU than the old Whisper polling approach.
    """
    model = _get_model()
    chunk_size = 1280  # 80ms at 16kHz — what OpenWakeWord expects

    # Check for tray shutdown signal (only matters in packaged .exe mode)
    try:
        from tray import should_shutdown
    except Exception:
        should_shutdown = lambda: False

    wake_display = WAKE_MODEL.replace("_", " ").title()
    print(f"Listening for wake word (say '{wake_display}')...")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                        blocksize=chunk_size) as stream:
        while True:
            if should_shutdown():
                raise SystemExit("Tray quit requested")

            data, _ = stream.read(chunk_size)
            audio = data.flatten()

            # Feed audio to the wake word model
            prediction = model.predict(audio)

            # Check if confidence exceeds threshold
            score = prediction[WAKE_MODEL]
            if score > WAKE_THRESHOLD:
                print(f"Wake word detected! (confidence: {score:.2f})")
                model.reset()  # Clear internal state for next detection
                return
