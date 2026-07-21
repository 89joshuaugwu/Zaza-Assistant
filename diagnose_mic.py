"""
Zaza Assistant — Mic Diagnostic
Run this standalone to check:
  1. Which microphones Windows sees, and which one is default
  2. What Vosk actually transcribes in real time (so we can see if it's
     picking up your voice at all, and what it hears instead of "hey zaza")

Run: python diagnose_mic.py
Talk normally, watch the terminal, Ctrl+C to stop.
"""

import json
import sounddevice as sd
from vosk import Model, KaldiRecognizer

from config import VOSK_MODEL_PATH, SAMPLE_RATE

print("=" * 60)
print("AVAILABLE AUDIO DEVICES")
print("=" * 60)
print(sd.query_devices())
print()
print(f"Default input device: {sd.query_devices(kind='input')['name']}")
print("=" * 60)
print()

print("Loading Vosk model...")
model = Model(VOSK_MODEL_PATH)
rec = KaldiRecognizer(model, SAMPLE_RATE)

import queue
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(f"[stream status: {status}]")
    q.put(bytes(indata))

print("Listening... speak now (say 'hey zaza' a few times). Ctrl+C to stop.\n")

with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16",
                        channels=1, callback=callback):
    try:
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "")
                if text:
                    print(f"FINAL:   '{text}'")
            else:
                partial = json.loads(rec.PartialResult())
                text = partial.get("partial", "")
                if text:
                    print(f"partial: '{text}'", end="\r")
    except KeyboardInterrupt:
        print("\n\nStopped.")
