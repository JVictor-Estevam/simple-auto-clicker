import sys

import customtkinter as ctk

try:
    from pynput.keyboard import Controller as KeyboardController, Key
    from pynput.mouse import Controller as MouseController
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    Key = None
    KeyboardController = None
    MouseController = None

DEFAULT_FORCE_STOP = "f7"
ALT_FORCE_STOP = "f8"

INTERVAL_PRESETS = (
    ("0.1s", 0.1),
    ("0.5s", 0.5),
    ("1s", 1.0),
    ("2s", 2.0),
    ("5s", 5.0),
)

CONTROL_H = 32
WINDOW_WIDTH = 420

# Theme
BG_APP = "#0F1117"
BG_PANEL = "#1A1B23"
BG_INPUT = "#111218"
BG_HOVER = "#25273A"
ACCENT = "#5865F2"
ACCENT_DIM = "#3442C4"
DANGER = "#ED4245"
DANGER_DIM = "#A12D2F"
SUCCESS = "#23A55A"
TEXT_PRI = "#F2F3F5"
TEXT_SEC = "#72767D"
BORDER = "#2E3144"
WARN = "#FAA61A"

FONT = "SF Pro" if sys.platform == "darwin" else "Segoe UI"

SPECIAL_KEYS: dict[str, object] = {}
if PYNPUT_AVAILABLE and Key is not None:
    SPECIAL_KEYS = {
        "enter": Key.enter,
        "space": Key.space,
        "tab": Key.tab,
        "backspace": Key.backspace,
        "delete": Key.delete,
        "escape": Key.esc,
        "up": Key.up,
        "down": Key.down,
        "left": Key.left,
        "right": Key.right,
        "home": Key.home,
        "end": Key.end,
        "page up": Key.page_up,
        "page down": Key.page_down,
        "insert": Key.insert,
        "f1": Key.f1,
        "f2": Key.f2,
        "f3": Key.f3,
        "f4": Key.f4,
        "f5": Key.f5,
        "f6": Key.f6,
        "f7": Key.f7,
        "f8": Key.f8,
        "f9": Key.f9,
        "f10": Key.f10,
        "f11": Key.f11,
        "f12": Key.f12,
        "ctrl": Key.ctrl,
        "alt": Key.alt,
        "shift": Key.shift,
        "win": Key.cmd,
        "caps lock": Key.caps_lock,
        "print screen": Key.print_screen,
        "scroll lock": Key.scroll_lock,
        "pause": Key.pause,
        "num lock": Key.num_lock,
    }

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

keyboard_controller = KeyboardController() if PYNPUT_AVAILABLE else None
mouse_controller = MouseController() if PYNPUT_AVAILABLE else None
