"""
Zaza Assistant — Main Loop

Flow:
  1. Sit idle listening for the wake word (OpenWakeWord — "Hey Jarvis")
  2. Once heard, record a short command
  3. Transcribe it with Whisper, send to the local LLM with tool definitions
  4. LLM either calls a tool (open app, get time, etc.) or replies directly
  5. Speak the result back
  6. Loop

Run: python main.py
Type-only mode (no mic): python main.py --text
"""

import sys
import os
import atexit
import traceback

import numpy as np
import sounddevice as sd

from config import ASSISTANT_NAME, WAKE_MODEL, BASE_DIR, SAMPLE_RATE
from text_to_speech import speak
from llm_brain import think


# When packaged with --noconsole there's no terminal to see print()/errors,
# so redirect stdout/stderr to a log file next to the exe.
if getattr(sys, "frozen", False):
    log_path = os.path.join(BASE_DIR, "zaza.log")
    log_file = open(log_path, "a", buffering=1, encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file
    atexit.register(log_file.close)


def _check_mic():
    """Quick startup mic check — records 1 second and shows volume level."""
    print("Checking microphone...")
    try:
        audio = sd.rec(
            int(SAMPLE_RATE * 1), samplerate=SAMPLE_RATE,
            channels=1, dtype="int16"
        )
        sd.wait()
        peak = int(np.abs(audio).max())
        avg = int(np.abs(audio).mean())

        if peak < 50:
            print("  WARNING: Mic seems silent (peak={peak}). Check Windows mic permissions.")
            print("  Settings > Privacy > Microphone > make sure it's ON")
            speak("Warning: your microphone seems silent. Check Windows mic permissions.")
        else:
            bars = "#" * min(avg // 100 + 1, 30)
            print(f"  Mic OK (peak={peak}, avg={avg}) [{bars}]")
    except Exception as e:
        print(f"  Mic check failed: {e}")
        speak("I couldn't access your microphone. Check that it's plugged in and enabled.")


def run_voice_mode():
    from wake_word import listen_for_wake_word
    from whisper_stt import listen_for_command

    if getattr(sys, "frozen", False):
        from tray import start_tray_in_background
        start_tray_in_background()

    _check_mic()

    wake_display = WAKE_MODEL.replace("_", " ").title()
    speak(f"{ASSISTANT_NAME} is online. Say '{wake_display}' to activate.")
    while True:
        try:
            listen_for_wake_word()
            speak("Yes?")
            command = listen_for_command()
            print(f"You said: {command}")

            if not command:
                speak("I didn't catch that.")
                continue

            if command.lower() in ("stop", "exit", "shut down", "goodbye"):
                speak("Going offline. Later.")
                break

            reply = think(command)
            speak(reply)

        except SystemExit:
            speak("Going offline. Later.")
            break
        except KeyboardInterrupt:
            speak("Shutting down.")
            break
        except Exception as e:
            print(traceback.format_exc())
            speak("I hit an error. Check the log for details.")


def run_text_mode():
    """Fallback mode — type commands instead of speaking them.
    Useful for testing without a mic, or if audio isn't set up yet."""
    print(f"{ASSISTANT_NAME} (text mode). Type 'exit' to quit.")
    while True:
        try:
            command = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoing offline.")
            break

        if not command:
            continue
        if command.lower() in ("stop", "exit", "quit", "shut down", "goodbye"):
            print(f"{ASSISTANT_NAME}: Later.")
            break

        reply = think(command)
        print(f"{ASSISTANT_NAME}: {reply}")


if __name__ == "__main__":
    if "--text" in sys.argv:
        run_text_mode()
    else:
        run_voice_mode()
