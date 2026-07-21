"""
Zaza Assistant — Wake Word Detection (dual-mode)

Supports two detection modes, automatically chosen based on WAKE_WORD:

1. OpenWakeWord (pre-trained) — for "hey jarvis", "alexa", "hey mycroft"
   Purpose-built neural model. Best accuracy, lowest CPU.

2. Whisper streaming (custom) — for ANY phrase like "hey josh"
   Continuous audio stream with energy-based speech detection +
   rolling-buffer Whisper transcription. No polling gaps.

The module auto-selects the best mode based on what WAKE_WORD is set to.
"""

import numpy as np
import sounddevice as sd
import time as _time

from config import SAMPLE_RATE, WAKE_MODE, WAKE_MODEL, WAKE_WORD, WAKE_THRESHOLD, ASSISTANT_NAME

# Pre-trained OpenWakeWord models — if WAKE_WORD matches one, we use it
_PRETRAINED_MODELS = {
    "hey jarvis": "hey_jarvis",
    "alexa": "alexa",
    "hey mycroft": "hey_mycroft",
}


# ── Mode 1: OpenWakeWord (pre-trained, best performance) ──

_oww_model = None


def _get_oww_model(model_name: str):
    """Lazy-load an OpenWakeWord pre-trained model."""
    global _oww_model
    if _oww_model is None:
        print(f"Loading OpenWakeWord model ({model_name})...")
        try:
            import openwakeword
            openwakeword.utils.download_models()
            from openwakeword.model import Model
            _oww_model = Model(wakeword_models=[model_name])
        except Exception as e:
            raise RuntimeError(
                f"Failed to load OpenWakeWord model '{model_name}': {e}\n"
                "Make sure openwakeword is installed: pip install openwakeword"
            ) from e
    return _oww_model


def _listen_openwakeword(model_name: str):
    """Pre-trained wake word detection — continuous 80ms streaming."""
    model = _get_oww_model(model_name)
    chunk_size = 1280  # 80ms at 16kHz

    try:
        from tray import should_shutdown
    except Exception:
        should_shutdown = lambda: False

    print(f"Listening for wake word: '{WAKE_WORD}' (OpenWakeWord mode)...")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                        blocksize=chunk_size) as stream:
        while True:
            if should_shutdown():
                raise SystemExit("Tray quit requested")

            data, _ = stream.read(chunk_size)
            audio = data.flatten()
            prediction = model.predict(audio)
            score = prediction[model_name]

            if score > WAKE_THRESHOLD:
                print(f"Wake word detected! (confidence: {score:.2f})")
                model.reset()
                return


# ── Mode 2: Whisper streaming (custom wake words) ─────────

_whisper_wake_model = None


def _get_whisper_wake_model():
    """Lazy-load a tiny Whisper model for custom wake word detection."""
    global _whisper_wake_model
    if _whisper_wake_model is None:
        print("Loading Whisper wake-word model (tiny.en)...")
        from faster_whisper import WhisperModel
        _whisper_wake_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    return _whisper_wake_model


def _listen_whisper_streaming():
    """Custom wake word detection via continuous streaming + Whisper.

    Unlike the old polling approach, this:
    - Streams audio continuously (no gaps between recordings)
    - Uses a rolling buffer so the wake word can span any position
    - Only runs Whisper when speech energy is detected (saves CPU)
    - Limits transcription to once per second (prevents CPU overload)
    """
    model = _get_whisper_wake_model()
    wake_lower = WAKE_WORD.lower()

    chunk_duration = 0.5  # 500ms per chunk
    chunk_size = int(SAMPLE_RATE * chunk_duration)
    buffer_seconds = 3.0  # rolling buffer length
    buffer_max_chunks = int(buffer_seconds / chunk_duration)
    energy_threshold = 300  # minimum energy to consider as speech
    min_transcribe_interval = 1.0  # at most one Whisper call per second

    try:
        from tray import should_shutdown
    except Exception:
        should_shutdown = lambda: False

    print(f"Listening for wake word: '{WAKE_WORD}' (Whisper streaming mode)...")

    buffer = []
    last_transcribe_time = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                        blocksize=chunk_size) as stream:
        while True:
            if should_shutdown():
                raise SystemExit("Tray quit requested")

            data, _ = stream.read(chunk_size)
            chunk = data.flatten()

            # Maintain rolling buffer
            buffer.append(chunk)
            if len(buffer) > buffer_max_chunks:
                buffer.pop(0)

            # Only transcribe when speech energy is detected
            energy = np.abs(chunk).mean()
            if energy < energy_threshold:
                continue

            # Rate-limit Whisper calls to once per second
            now = _time.time()
            if (now - last_transcribe_time) < min_transcribe_interval:
                continue
            last_transcribe_time = now

            # Transcribe the rolling buffer
            audio = np.concatenate(buffer).astype(np.float32) / 32768.0
            segments, _ = model.transcribe(audio, language="en", beam_size=1)
            text = " ".join(seg.text.strip() for seg in segments).lower()

            if wake_lower in text:
                print(f"Wake word detected! (heard: '{text}')")
                buffer.clear()
                return


# ── Public API ────────────────────────────────────────────


def get_active_wake_phrase() -> str:
    """Returns the wake phrase the user should say, based on current mode."""
    if WAKE_MODE == "model":
        # Convert model name to spoken phrase: "hey_jarvis" → "Hey Jarvis"
        return WAKE_MODEL.replace("_", " ").title()
    return WAKE_WORD.title()


def listen_for_wake_word():
    """Blocks until the wake word/phrase is heard.

    Uses WAKE_MODE from config to decide the detection method:
    - "model"  → OpenWakeWord pre-trained (hey_jarvis, alexa, hey_mycroft)
    - "custom" → Whisper streaming (any phrase like "hey josh")
    """
    if WAKE_MODE == "model":
        _listen_openwakeword(WAKE_MODEL)
    else:
        _listen_whisper_streaming()
