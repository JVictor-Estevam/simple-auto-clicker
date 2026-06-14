import json
import os
import sys

DEFAULT_SETTINGS = {
    "action_type": "mouse",
    "mouse_click_mode": "free",
    "click_x": "0",
    "click_y": "0",
    "key": "space",
    "interval": "1.0",
    "repeat": False,
    "repeat_count": "10",
}


def get_settings_path() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        folder = os.path.join(base, "SimpleAutoClicker")
    else:
        folder = os.path.join(os.path.expanduser("~"), ".simple-autoclicker")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "settings.json")


def load_settings() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    try:
        with open(get_settings_path(), encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            settings.update(data)
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return settings


def save_settings(data: dict) -> None:
    try:
        with open(get_settings_path(), "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
    except OSError:
        pass
