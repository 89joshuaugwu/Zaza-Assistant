"""
Zaza Assistant — Main Loop

Flow:
  1. Startup: check mic, greet user (references past sessions if any)
  2. Listen for wake word ("Hey Jarvis" via OpenWakeWord)
  3. Enter conversation mode — keep talking without wake word
  4. After 30 seconds of silence, go back to listening for wake word
  5. "Stop" / "exit" shuts down entirely

Run: python main.py
Type-only mode (no mic): python main.py --text
"""

import sys
import os
import atexit
import traceback
import time as _time
from datetime import datetime

import numpy as np
import sounddevice as sd

from config import ASSISTANT_NAME, BASE_DIR, SAMPLE_RATE, CONVERSATION_TIMEOUT
from text_to_speech import speak, wait_until_done
from llm_brain import think


# When packaged with --noconsole there's no terminal to see print()/errors,
# so redirect stdout/stderr to a log file next to the exe.
if getattr(sys, "frozen", False):
    log_path = os.path.join(BASE_DIR, "zaza.log")
    log_file = open(log_path, "a", buffering=1, encoding="utf-8")
    sys.stdout = log_file
    sys.stderr = log_file
    atexit.register(log_file.close)


# Words that exit the assistant completely
EXIT_WORDS = {"stop", "exit", "shut down", "goodbye", "quit"}

# Words that end the conversation but keep listening for wake word
END_CONVERSATION_WORDS = {"nevermind", "never mind", "that's all", "thanks",
                          "thank you", "bye", "i'm done", "that will be all"}


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
            print(f"  WARNING: Mic seems silent (peak={peak}). Check Windows mic permissions.")
            print("  Settings > Privacy > Microphone > make sure it's ON")
            speak("Warning: your microphone seems silent. Check Windows mic permissions.")
        else:
            bars = "#" * min(avg // 100 + 1, 30)
            print(f"  Mic OK (peak={peak}, avg={avg}) [{bars}]")
    except Exception as e:
        print(f"  Mic check failed: {e}")
        speak("I couldn't access your microphone. Check that it's plugged in and enabled.")


def _startup_greeting():
    """Smart greeting based on time of day and conversation history."""
    from memory import get_last_session_info

    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    from wake_word import get_active_wake_phrase
    wake_display = get_active_wake_phrase()
    session = get_last_session_info()

    if session and session.get("timestamp"):
        last_dt = session["timestamp"]
        now = datetime.now()
        delta = now - last_dt

        if delta.total_seconds() < 3600:
            speak(f"I'm back! Say '{wake_display}' when you need me.")
        elif delta.days == 0:
            speak(f"{greeting}! {ASSISTANT_NAME} is online again. Say '{wake_display}' when you need me.")
        elif delta.days == 1:
            speak(f"{greeting}! Haven't talked since yesterday. Say '{wake_display}' and I'm all yours.")
        else:
            speak(f"{greeting}! It's been a while — {ASSISTANT_NAME} is back online. Say '{wake_display}' to get started.")
    else:
        speak(f"{greeting}! I'm {ASSISTANT_NAME}, your assistant. Say '{wake_display}' to get started.")
        
    wait_until_done()


def run_voice_mode():
    from wake_word import listen_for_wake_word
    from whisper_stt import listen_for_command

    if getattr(sys, "frozen", False):
        from tray import start_tray_in_background
        start_tray_in_background()

    _check_mic()
    _startup_greeting()

    while True:
        try:
            # ── Phase 1: Wait for wake word ──
            try:
                from gui import signals
                signals.state_changed.emit("sleeping")
                signals.text_updated.emit("Sleeping...")
            except ImportError: pass
            
            listen_for_wake_word()
            
            try:
                from gui import signals
                signals.state_changed.emit("speaking")
                signals.text_updated.emit("Yes?")
            except ImportError: pass
            
            speak("Yes?")
            wait_until_done()

            # ── Phase 2: Conversation mode ──
            last_activity = _time.time()

            while True:
                try:
                    from gui import signals
                    signals.state_changed.emit("listening")
                    signals.text_updated.emit("Listening...")
                except ImportError: pass
                
                command = listen_for_command()

                if not command:
                    elapsed = _time.time() - last_activity
                    if elapsed >= CONVERSATION_TIMEOUT:
                        try:
                            from gui import signals
                            signals.state_changed.emit("speaking")
                        except ImportError: pass
                        speak("I'll be here when you need me.")
                        wait_until_done()
                        break
                    continue

                last_activity = _time.time()
                print(f"You said: {command}")
                
                try:
                    from gui import signals
                    signals.state_changed.emit("thinking")
                    signals.text_updated.emit(f"You: {command}")
                except ImportError: pass

                lower = command.lower().strip()
                if lower in EXIT_WORDS:
                    speak("Going offline. Later.")
                    wait_until_done()
                    return

                if lower in END_CONVERSATION_WORDS:
                    speak("Alright, I'm here if you need me.")
                    wait_until_done()
                    break

                reply = think(command)
                
                try:
                    from gui import signals
                    signals.state_changed.emit("speaking")
                    signals.text_updated.emit("Josh is replying...")
                except ImportError: pass
                
                wait_until_done()

        except SystemExit:
            speak("Going offline. Later.")
            wait_until_done()
            break
        except KeyboardInterrupt:
            speak("Shutting down.")
            wait_until_done()
            break
        except Exception as e:
            print(traceback.format_exc())
            speak("I hit an error. Check the log for details.")
            wait_until_done()


def run_text_mode():
    """Fallback mode — type commands instead of speaking them.
    Useful for testing without a mic, or if audio isn't set up yet.
    Text mode ALSO speaks replies aloud so you can hear the TTS."""
    _startup_greeting()
    print(f"{ASSISTANT_NAME} (text mode). Type 'exit' to quit.")
    print("Conversation mode is always active in text mode — just keep typing.\n")
    while True:
        try:
            command = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoing offline.")
            break

        if not command:
            continue
        if command.lower() in EXIT_WORDS:
            speak("Later.")
            break

        reply = think(command)
        wait_until_done()


if __name__ == "__main__":
    if "--text" in sys.argv:
        run_text_mode()
    elif "--cli" in sys.argv:
        run_voice_mode()
    else:
        try:
            from gui import launch_gui
            launch_gui()
        except ImportError as e:
            print(f"Could not load GUI ({e}). Falling back to CLI mode.")
            run_voice_mode()
