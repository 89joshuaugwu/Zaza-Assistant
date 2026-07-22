import sys
import threading
import queue
import time
import webview
import os
import dotenv

class Api:
    def __init__(self):
        self.dashboard_window = None

    def open_dashboard(self):
        if self.dashboard_window is None:
            ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'dashboard.html')
            self.dashboard_window = webview.create_window(
                'Zaza Settings',
                ui_path,
                width=400,
                height=500,
                frameless=True,
                easy_drag=False
            )
            self.dashboard_window.events.closed += self.on_dashboard_closed

    def close_dashboard(self):
        if self.dashboard_window:
            self.dashboard_window.destroy()
            self.dashboard_window = None

    def on_dashboard_closed(self):
        self.dashboard_window = None

    def get_settings(self):
        from config import WAKE_WORD, WAKE_MODEL, OLLAMA_MODEL
        return {
            'WAKE_WORD': WAKE_WORD,
            'WAKE_MODEL': WAKE_MODEL,
            'OLLAMA_MODEL': OLLAMA_MODEL
        }

    def save_settings(self, new_settings):
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        for key, value in new_settings.items():
            dotenv.set_key(env_path, key, value)
        print("Settings saved! Restart required to take full effect.")


class Signals:
    def __init__(self):
        self.queue = queue.Queue()

    class SignalProxy:
        def __init__(self, name, q):
            self.name = name
            self.q = q
        def emit(self, value):
            self.q.put((self.name, value))

    @property
    def state_changed(self):
        return self.SignalProxy("state_changed", self.queue)

    @property
    def text_updated(self):
        return self.SignalProxy("text_updated", self.queue)

signals = Signals()

def assistant_worker():
    from main import run_voice_mode
    try:
        run_voice_mode()
    except Exception as e:
        print(f"Assistant thread crashed: {e}")

def signal_processor(window):
    while True:
        try:
            msg, val = signals.queue.get(timeout=0.1)
            if msg == "state_changed":
                window.evaluate_js(f"setState('{val}')")
            elif msg == "text_updated":
                val = val.replace("'", "\\'").replace('"', '\\"')
                window.evaluate_js(f"setText('{val}')")
        except queue.Empty:
            pass

def launch_gui():
    ui_path = os.path.join(os.path.dirname(__file__), 'ui', 'index.html')
    
    api = Api()
    
    window = webview.create_window(
        'Zaza Assistant', 
        ui_path, 
        transparent=True, 
        frameless=True, 
        width=400, 
        height=300, 
        js_api=api,
        on_top=True
    )

    def on_loaded():
        threading.Thread(target=assistant_worker, daemon=True).start()
        threading.Thread(target=signal_processor, args=(window,), daemon=True).start()

    window.events.loaded += on_loaded

    webview.start(gui='edgechromium', debug=False)

if __name__ == "__main__":
    launch_gui()
