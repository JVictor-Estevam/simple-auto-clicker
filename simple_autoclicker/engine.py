import threading
import time
from typing import Callable

from simple_autoclicker.action_queue import execute_step
from simple_autoclicker.constants import (
    PYNPUT_AVAILABLE,
    SPECIAL_KEYS,
    keyboard_controller,
    mouse_controller,
)

if PYNPUT_AVAILABLE:
    from pynput.mouse import Button


class AutoClicker:
    """Runs repeated mouse clicks, key presses, or action queues on a background thread."""

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

    def start_queue(
        self,
        steps: list[dict[str, str]],
        cycle_interval: float,
        repeat: bool,
        repeat_count: int,
        on_tick: Callable[[int, int, int], None],
        on_done: Callable[[], None],
    ) -> None:
        self.running = True
        self._thread = threading.Thread(
            target=self._queue_loop,
            args=(steps, cycle_interval, repeat, repeat_count, on_tick, on_done),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self.running = False

    def _sleep(self, seconds: float) -> None:
        elapsed = 0.0
        while elapsed < seconds and self.running:
            time.sleep(0.05)
            elapsed += 0.05

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

            self._sleep(interval)

        self.running = False
        on_done()

    def _queue_loop(
        self,
        steps: list[dict[str, str]],
        cycle_interval: float,
        repeat: bool,
        repeat_count: int,
        on_tick: Callable[[int, int, int], None],
        on_done: Callable[[], None],
    ) -> None:
        cycles = 0
        total_steps = len(steps)

        while self.running:
            if repeat and cycles >= repeat_count:
                break

            for index, step in enumerate(steps):
                if not self.running:
                    break
                try:
                    execute_step(step)
                except Exception:
                    pass

                on_tick(cycles + 1, index + 1, total_steps)

                if index < total_steps - 1:
                    try:
                        delay = float(step["delay_after"].replace(",", "."))
                    except (ValueError, AttributeError):
                        delay = 0.0
                    self._sleep(max(0.0, delay))

            cycles += 1
            if repeat and cycles >= repeat_count:
                break
            self._sleep(cycle_interval)

        self.running = False
        on_done()
