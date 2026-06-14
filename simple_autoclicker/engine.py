import threading
import time

from simple_autoclicker.constants import (
    PYNPUT_AVAILABLE,
    SPECIAL_KEYS,
    keyboard_controller,
    mouse_controller,
)

if PYNPUT_AVAILABLE:
    from pynput.mouse import Button


class AutoClicker:
    """Runs repeated mouse clicks or key presses on a background thread."""

    def __init__(self) -> None:
        self.running = False
        self._thread: threading.Thread | None = None

    def start(
        self,
        action_type: str,
        key_value: str,
        interval: float,
        repeat: bool,
        repeat_count: int,
        on_tick,
        on_done,
        mouse_mode: str = "free",
        click_x: int = 0,
        click_y: int = 0,
    ) -> None:
        self.running = True
        self._thread = threading.Thread(
            target=self._loop,
            args=(
                action_type,
                key_value,
                interval,
                repeat,
                repeat_count,
                on_tick,
                on_done,
                mouse_mode,
                click_x,
                click_y,
            ),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self.running = False

    def _loop(
        self,
        action_type: str,
        key_value: str,
        interval: float,
        repeat: bool,
        repeat_count: int,
        on_tick,
        on_done,
        mouse_mode: str,
        click_x: int,
        click_y: int,
    ) -> None:
        count = 0
        while self.running:
            if repeat and count >= repeat_count:
                break
            try:
                if action_type == "mouse" and mouse_controller is not None:
                    if mouse_mode == "coords":
                        mouse_controller.position = (click_x, click_y)
                    mouse_controller.click(Button.left)
                elif action_type == "key" and keyboard_controller is not None:
                    if key_value in SPECIAL_KEYS:
                        key = SPECIAL_KEYS[key_value]
                        keyboard_controller.press(key)
                        keyboard_controller.release(key)
                    elif len(key_value) == 1:
                        keyboard_controller.press(key_value)
                        keyboard_controller.release(key_value)
            except Exception:
                pass

            count += 1
            on_tick(count)

            elapsed = 0.0
            while elapsed < interval and self.running:
                time.sleep(0.05)
                elapsed += 0.05

        self.running = False
        on_done()
