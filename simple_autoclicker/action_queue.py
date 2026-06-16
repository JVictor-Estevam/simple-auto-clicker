"""Action queue model, validation, and step execution."""

from __future__ import annotations

from typing import Any

from simple_autoclicker.constants import (
    PYNPUT_AVAILABLE,
    SPECIAL_KEYS,
    keyboard_controller,
    mouse_controller,
)

if PYNPUT_AVAILABLE:
    from pynput.mouse import Button

MAX_QUEUE_SIZE = 10
DEFAULT_QUEUE_STEP: dict[str, str] = {
    "type": "mouse",
    "x": "0",
    "y": "0",
    "key": "space",
    "delay_after": "1.0",
}


def normalize_step(raw: dict[str, Any]) -> dict[str, str]:
    step_type = str(raw.get("type", "mouse")).lower()
    if step_type not in ("mouse", "key"):
        step_type = "mouse"
    return {
        "type": step_type,
        "x": str(raw.get("x", "0")),
        "y": str(raw.get("y", "0")),
        "key": str(raw.get("key", "space")),
        "delay_after": str(raw.get("delay_after", "1.0")),
    }


def normalize_queue(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    steps = [normalize_step(item) for item in raw if isinstance(item, dict)]
    return steps[:MAX_QUEUE_SIZE]


def validate_queue(steps: list[dict[str, str]]) -> str | None:
    if not steps:
        return "Add at least one action to the queue."
    if len(steps) > MAX_QUEUE_SIZE:
        return f"The queue supports at most {MAX_QUEUE_SIZE} actions."

    for index, step in enumerate(steps, start=1):
        if step["type"] == "mouse":
            try:
                int(step["x"].strip())
                int(step["y"].strip())
            except (ValueError, AttributeError):
                return f"Step {index}: enter valid X and Y coordinates."
        else:
            key = step["key"].strip().lower()
            if not key:
                return f"Step {index}: enter a key."
            if len(key) > 1 and key not in SPECIAL_KEYS:
                return f"Step {index}: '{key}' is not a recognized special key."

        try:
            delay = float(step["delay_after"].replace(",", "."))
        except (ValueError, AttributeError):
            return f"Step {index}: invalid wait time."
        if delay < 0:
            return f"Step {index}: wait time cannot be negative."

    return None


def queue_uses_f7(steps: list[dict[str, str]]) -> bool:
    return any(
        step["type"] == "key" and step["key"].strip().lower() == "f7"
        for step in steps
    )


def execute_step(step: dict[str, str]) -> None:
    if not PYNPUT_AVAILABLE:
        return

    if step["type"] == "mouse" and mouse_controller is not None:
        x = int(step["x"].strip())
        y = int(step["y"].strip())
        mouse_controller.position = (x, y)
        mouse_controller.click(Button.left)
        return

    if step["type"] == "key" and keyboard_controller is not None:
        key_value = step["key"].strip().lower()
        if key_value in SPECIAL_KEYS:
            key = SPECIAL_KEYS[key_value]
            keyboard_controller.press(key)
            keyboard_controller.release(key)
        elif len(key_value) == 1:
            keyboard_controller.press(key_value)
            keyboard_controller.release(key_value)
