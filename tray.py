"""
Zaza Assistant — Tray Icon
Since the packaged .exe runs with --noconsole (no visible window), this puts
a small icon in the Windows system tray so you can see it's alive and quit
it without Task Manager.
"""

import threading
from PIL import Image, ImageDraw
import pystray

from config import ASSISTANT_NAME

_icon = None


def _make_icon_image():
    # Simple generated icon — a filled circle with "Z" — no external asset needed
    img = Image.new("RGB", (64, 64), color=(27, 43, 107))  # navy, matches PenWork4Me brand
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 60, 60), fill=(245, 166, 35))  # gold circle
    d.text((22, 18), "Z", fill=(27, 43, 107))
    return img


def _on_quit(icon, _item):
    icon.stop()
    # Hard exit — the voice loop runs in the main thread and won't check
    # a flag mid-listen, so we terminate the process outright.
    import os
    os._exit(0)


def start_tray():
    """Runs the tray icon loop. Call this in a background thread from main.py."""
    global _icon
    menu = pystray.Menu(
        pystray.MenuItem(f"{ASSISTANT_NAME} is running", None, enabled=False),
        pystray.MenuItem("Quit", _on_quit),
    )
    _icon = pystray.Icon(ASSISTANT_NAME, _make_icon_image(), ASSISTANT_NAME, menu)
    _icon.run()


def start_tray_in_background():
    t = threading.Thread(target=start_tray, daemon=True)
    t.start()
    return t
