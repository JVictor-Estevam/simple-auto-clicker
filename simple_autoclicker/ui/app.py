"""CustomTkinter UI layer for Simple AutoClicker."""

import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from simple_autoclicker.constants import (
    ACCENT,
    ACCENT_DIM,
    ALT_FORCE_STOP,
    BG_APP,
    BG_HOVER,
    BG_INPUT,
    BG_PANEL,
    BORDER,
    CONTROL_H,
    DANGER,
    DANGER_DIM,
    DEFAULT_FORCE_STOP,
    FONT,
    INTERVAL_PRESETS,
    PYNPUT_AVAILABLE,
    SPECIAL_KEYS,
    SUCCESS,
    TEXT_PRI,
    TEXT_SEC,
    WARN,
    WINDOW_WIDTH,
    mouse_controller,
)
from simple_autoclicker.action_queue import (
    DEFAULT_QUEUE_STEP,
    MAX_QUEUE_SIZE,
    normalize_queue,
    queue_uses_f7,
    validate_queue,
)
from simple_autoclicker.engine import AutoClicker
from simple_autoclicker.resources import asset_path
from simple_autoclicker.screen import get_virtual_screen_bounds
from simple_autoclicker.settings import load_settings, save_settings
from simple_autoclicker.validation import (
    is_valid_decimal,
    is_valid_signed_int,
    is_valid_unsigned_int,
)

if PYNPUT_AVAILABLE:
    from pynput import keyboard, mouse
    from pynput.keyboard import Key
    from pynput.mouse import Button

__all__ = ["App"]


class App(ctk.CTk):
    # --- Window setup ---

    def __init__(self):
        super().__init__()
        self.title("Simple AutoClicker")
        self.configure(fg_color=BG_APP)
        self.resizable(False, False)
        self._set_window_icon()
        self._set_window_alpha(0)

        self.clicker = AutoClicker()
        self.automation_mode = "single"
        self.action_type = "mouse"
        self.mouse_click_mode = "free"
        self._is_running = False
        self._queue_rows: list[dict] = []
        self._queue_pick_index: int | None = None
        self._queue_key_capture_index: int | None = None
        self._stop_listener = None
        self._last_key = "space"
        self._coord_pick_active = False
        self._coord_mouse_listener = None
        self._coord_kb_listener = None
        self._coord_tooltip = None
        self._key_capture_listener = None
        self._key_capture_active = False
        self._preset_buttons = {}

        self._build_ui()
        self._load_persisted_settings()
        self._apply_window_geometry()
        self._set_window_alpha(1)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_window_alpha(self, value):
        try:
            self.attributes("-alpha", value)
        except tk.TclError:
            pass

    def _set_window_icon(self):
        self._icon_image = None
        ico = asset_path("icon.ico")
        png = asset_path("icon.png")
        try:
            if sys.platform == "win32" and ico.is_file():
                self.iconbitmap(str(ico))
            elif png.is_file():
                self._icon_image = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._icon_image)
        except tk.TclError:
            pass

    def _build_ui(self):
        self._build_header()
        self._build_footer()
        self._build_body()
        self._select_action("mouse")
        self._update_hotkey_hint()

    def _apply_window_geometry(self):
        self.update_idletasks()
        w = WINDOW_WIDTH
        h = max(self.winfo_reqheight(), 1)
        x = (self.winfo_screenwidth() - w) // 2
        y = max(0, (self.winfo_screenheight() - h) // 2 - 20)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _refresh_geometry(self):
        self.update_idletasks()
        geo = self.geometry()
        if "+" not in geo:
            return
        parts = geo.split("+")
        w = WINDOW_WIDTH
        h = max(self.winfo_reqheight(), 1)
        x, y = int(parts[1]), int(parts[2])
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color=BG_PANEL, height=44, corner_radius=0)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)

        title_row = ctk.CTkFrame(self.header, fg_color="transparent")
        title_row.pack(fill="both", expand=True, padx=16, pady=8)

        ctk.CTkLabel(
            title_row,
            text="Simple AutoClicker",
            font=(FONT, 14, "bold"),
            text_color=TEXT_PRI,
        ).pack(side="left")

        self.state_indicator = ctk.CTkFrame(title_row, fg_color="transparent")
        self.state_indicator.pack(side="right")

        self.state_dot = ctk.CTkFrame(
            self.state_indicator, width=8, height=8, corner_radius=4, fg_color=TEXT_SEC,
        )
        self.state_dot.pack(side="left", padx=(0, 6))
        self.state_dot.pack_propagate(False)

        self.state_label = ctk.CTkLabel(
            self.state_indicator,
            text="Idle",
            font=(FONT, 10),
            text_color=TEXT_SEC,
        )
        self.state_label.pack(side="left")

    def _build_footer(self):
        self.footer = ctk.CTkFrame(
            self,
            fg_color=BG_PANEL,
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
        )
        self.footer.pack(side="bottom", fill="x")

        footer_inner = ctk.CTkFrame(self.footer, fg_color="transparent")
        footer_inner.pack(fill="x", padx=16, pady=12)

        status_wrap = ctk.CTkFrame(footer_inner, fg_color=BG_INPUT, height=28, corner_radius=6)
        status_wrap.pack(fill="x")
        status_wrap.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        self.tick_var = tk.StringVar(value="")

        self.status_label = ctk.CTkLabel(
            status_wrap,
            textvariable=self.status_var,
            font=(FONT, 9),
            text_color=TEXT_SEC,
        )
        self.status_label.pack(side="left", padx=10, pady=4)

        self.tick_label = ctk.CTkLabel(
            status_wrap,
            textvariable=self.tick_var,
            font=(FONT, 9, "bold"),
            text_color=TEXT_SEC,
        )
        self.tick_label.pack(side="right", padx=10, pady=4)

        self.action_btn = ctk.CTkButton(
            footer_inner,
            text="Start",
            height=44,
            corner_radius=8,
            font=(FONT, 13, "bold"),
            fg_color=ACCENT,
            hover_color=ACCENT_DIM,
            command=self._start,
        )
        self.action_btn.pack(fill="x", pady=(8, 0))

    def _build_body(self):
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(side="top", fill="x", padx=16, pady=(8, 4))
        self.body.grid_columnconfigure(0, weight=1)

        self._build_action_card(self.body)
        self._build_timing_card(self.body)

    def _on_close(self):
        self.clicker.stop()
        self._stop_force_stop_listener()
        if self._key_capture_active and self._key_capture_listener is not None:
            try:
                self._key_capture_listener.stop()
            except Exception:
                pass
        if self._coord_pick_active:
            self._cleanup_coord_pick()
        self._save_persisted_settings()
        self.destroy()

    # --- Layout helpers ---

    def _card(self, parent, title):
        wrapper = ctk.CTkFrame(
            parent,
            fg_color=BG_PANEL,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        wrapper.pack(fill="x", pady=(0, 8))

        inner = ctk.CTkFrame(wrapper, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(
            inner,
            text=title,
            font=(FONT, 11, "bold"),
            text_color=TEXT_PRI,
        ).pack(anchor="w", pady=(0, 8))

        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(fill="x")
        return wrapper, content

    def _grid_cell(self, parent, row, col, padx=(0, 0), rowspan=1):
        cell = ctk.CTkFrame(parent, fg_color="transparent", height=CONTROL_H)
        cell.grid(row=row, column=col, padx=padx, rowspan=rowspan, sticky="nw")
        cell.pack_propagate(False)
        return cell

    def _pack_inline_label(self, parent, text, padx=(0, 8)):
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=(FONT, 10),
            text_color=TEXT_SEC,
        )
        label.pack(side="left", padx=padx, pady=7)
        return label

    def _bind_numeric_entry(self, entry, mode):
        validators = {
            "decimal": is_valid_decimal,
            "unsigned_int": is_valid_unsigned_int,
            "signed_int": is_valid_signed_int,
        }
        validate = validators[mode]
        vcmd = (self.register(lambda proposed: validate(proposed)), "%P")
        entry._entry.configure(validate="key", validatecommand=vcmd)

    # --- Action panel ---

    def _build_action_card(self, parent):
        _, content = self._card(parent, "Action")

        self.mode_segment = ctk.CTkSegmentedButton(
            content,
            values=["Single", "Action queue"],
            height=32,
            font=(FONT, 11),
            fg_color=BG_INPUT,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_DIM,
            unselected_color=BG_HOVER,
            unselected_hover_color=BG_INPUT,
            text_color=TEXT_PRI,
            command=self._select_automation_mode_label,
        )
        self.mode_segment.set("Single")
        self.mode_segment.pack(fill="x")

        self.single_panel = ctk.CTkFrame(content, fg_color="transparent")
        self.single_panel.pack(fill="x", pady=(8, 0))

        self.action_segment = ctk.CTkSegmentedButton(
            self.single_panel,
            values=["Mouse", "Key"],
            height=32,
            font=(FONT, 11),
            fg_color=BG_INPUT,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_DIM,
            unselected_color=BG_HOVER,
            unselected_hover_color=BG_INPUT,
            text_color=TEXT_PRI,
            command=self._select_action_label,
        )
        self.action_segment.set("Mouse")
        self.action_segment.pack(fill="x")

        self.action_detail = ctk.CTkFrame(self.single_panel, fg_color="transparent")
        self.action_detail.pack(fill="x", pady=(8, 0))

        self.mouse_panel = ctk.CTkFrame(self.action_detail, fg_color="transparent")
        self.mouse_panel.pack(fill="x")

        switch_row = ctk.CTkFrame(self.mouse_panel, fg_color="transparent")
        switch_row.pack(fill="x")

        self.fixed_pos_var = tk.BooleanVar(value=False)
        self.fixed_pos_switch = ctk.CTkSwitch(
            switch_row,
            text="Fixed position (X, Y)",
            variable=self.fixed_pos_var,
            font=(FONT, 10),
            text_color=TEXT_PRI,
            fg_color=ACCENT,
            progress_color=ACCENT_DIM,
            button_color=TEXT_PRI,
            button_hover_color=TEXT_SEC,
            command=self._toggle_fixed_position,
        )
        self.fixed_pos_switch.pack(anchor="w")

        self.coords_frame = ctk.CTkFrame(self.mouse_panel, fg_color="transparent")
        self.coords_frame.pack(fill="x", pady=(8, 0))
        self.coords_frame.pack_forget()

        coords_row = ctk.CTkFrame(self.coords_frame, fg_color="transparent")
        coords_row.pack(fill="x", anchor="w")

        self.click_x_var = tk.StringVar(value="0")
        self.click_y_var = tk.StringVar(value="0")

        for col_idx, label in enumerate(("X", "Y")):
            ctk.CTkLabel(
                coords_row,
                text=label,
                font=(FONT, 9, "bold"),
                text_color=TEXT_SEC,
            ).grid(
                row=0,
                column=col_idx,
                sticky="w",
                padx=(0 if col_idx == 0 else 8, 0),
                pady=(0, 4),
            )

        self.click_x_entry = ctk.CTkEntry(
            coords_row,
            textvariable=self.click_x_var,
            width=68,
            height=CONTROL_H,
            corner_radius=6,
            font=(FONT, 12, "bold"),
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRI,
            justify="center",
        )
        self.click_x_entry.grid(row=1, column=0, sticky="w")
        self._bind_numeric_entry(self.click_x_entry, "signed_int")

        self.click_y_entry = ctk.CTkEntry(
            coords_row,
            textvariable=self.click_y_var,
            width=68,
            height=CONTROL_H,
            corner_radius=6,
            font=(FONT, 12, "bold"),
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRI,
            justify="center",
        )
        self.click_y_entry.grid(row=1, column=1, sticky="w", padx=(8, 0))
        self._bind_numeric_entry(self.click_y_entry, "signed_int")

        pick_cell = self._grid_cell(coords_row, 1, 2, padx=(8, 0))
        self.pick_btn = ctk.CTkButton(
            pick_cell,
            text="Pick",
            width=72,
            height=CONTROL_H,
            corner_radius=6,
            font=(FONT, 10),
            fg_color=BG_HOVER,
            hover_color=BG_INPUT,
            text_color=ACCENT,
            command=self._capture_mouse_position,
        )
        self.pick_btn.pack(fill="both", expand=True)

        self.key_panel = ctk.CTkFrame(self.action_detail, fg_color="transparent")
        self.key_panel.pack_forget()

        key_row = ctk.CTkFrame(self.key_panel, fg_color="transparent")
        key_row.pack(fill="x")
        key_row.grid_columnconfigure(0, weight=1)

        self.key_var = tk.StringVar(value="space")
        self.key_var.trace_add("write", lambda *_: self._on_key_changed())

        self.key_entry = ctk.CTkEntry(
            key_row,
            textvariable=self.key_var,
            height=CONTROL_H,
            corner_radius=6,
            font=(FONT, 14, "bold"),
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRI,
            placeholder_text="e.g. a, enter, space, f5",
            placeholder_text_color=TEXT_SEC,
        )
        self.key_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.key_entry.bind("<FocusIn>", lambda e: self.after(10, self._select_key_entry))

        self.capture_key_btn = ctk.CTkButton(
            key_row,
            text="Capture key",
            width=100,
            height=CONTROL_H,
            corner_radius=6,
            font=(FONT, 10),
            fg_color=BG_HOVER,
            hover_color=BG_INPUT,
            text_color=ACCENT,
            command=self._capture_key,
        )
        self.capture_key_btn.grid(row=0, column=1)

        self.hotkey_var = tk.StringVar()
        self.hotkey_label = ctk.CTkLabel(
            content,
            textvariable=self.hotkey_var,
            font=(FONT, 9),
            text_color=TEXT_SEC,
            wraplength=400,
            justify="left",
        )

        self.queue_panel = ctk.CTkFrame(content, fg_color="transparent")
        self._build_queue_panel(self.queue_panel)

        self.hotkey_label.pack(anchor="w", pady=(8, 0))

        self._update_key_section_state()

    def _select_action_label(self, label):
        action = "mouse" if label == "Mouse" else "key"
        self._select_action(action)

    # --- Action queue panel ---

    def _build_queue_panel(self, parent):
        parent.pack_forget()

        hint = ctk.CTkLabel(
            parent,
            text="Build a sequence (up to 10 steps). Each step can wait before the next. "
            "The full sequence repeats at the cycle interval in Timing.",
            font=(FONT, 9),
            text_color=TEXT_SEC,
            wraplength=400,
            justify="left",
        )
        hint.pack(anchor="w", pady=(0, 8))

        self.queue_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color=BG_INPUT,
            corner_radius=8,
            height=180,
            border_width=1,
            border_color=BORDER,
        )
        self.queue_scroll.pack(fill="x")
        self.queue_steps_frame = self.queue_scroll

        controls = ctk.CTkFrame(parent, fg_color="transparent")
        controls.pack(fill="x", pady=(8, 0))

        self.queue_add_btn = ctk.CTkButton(
            controls,
            text="+ Add step",
            height=30,
            corner_radius=6,
            font=(FONT, 10, "bold"),
            fg_color=BG_HOVER,
            hover_color=BG_INPUT,
            text_color=ACCENT,
            command=self._queue_add_step,
        )
        self.queue_add_btn.pack(side="left")

        self.queue_count_label = ctk.CTkLabel(
            controls,
            text="0/10 steps",
            font=(FONT, 9),
            text_color=TEXT_SEC,
        )
        self.queue_count_label.pack(side="right", pady=6)

    def _select_automation_mode_label(self, label):
        mode = "queue" if label == "Action queue" else "single"
        self._select_automation_mode(mode)

    def _select_automation_mode(self, mode):
        self.automation_mode = mode
        label = "Action queue" if mode == "queue" else "Single"
        if hasattr(self, "mode_segment"):
            self.mode_segment.set(label)

        if mode == "queue":
            self.single_panel.pack_forget()
            self.queue_panel.pack(fill="x", pady=(8, 0))
            if not self._queue_rows:
                self._queue_add_step()
        else:
            self.queue_panel.pack_forget()
            self.single_panel.pack(fill="x", pady=(8, 0))

        self._update_interval_hint()
        self._update_key_section_state()
        self._update_hotkey_hint()
        self._refresh_geometry()

    def _queue_snapshot(self) -> list[dict[str, str]]:
        steps = []
        for row in self._queue_rows:
            steps.append({
                "type": row["type_var"].get(),
                "x": row["x_var"].get(),
                "y": row["y_var"].get(),
                "key": row["key_var"].get(),
                "delay_after": row["delay_var"].get(),
            })
        return steps

    def _queue_renumber(self):
        for index, row in enumerate(self._queue_rows, start=1):
            row["index_label"].configure(text=str(index))
        count = len(self._queue_rows)
        self.queue_count_label.configure(text=f"{count}/{MAX_QUEUE_SIZE} steps")
        self.queue_add_btn.configure(state="normal" if count < MAX_QUEUE_SIZE else "disabled")

    def _queue_add_step(self, step_data: dict | None = None):
        if len(self._queue_rows) >= MAX_QUEUE_SIZE:
            return

        data = dict(DEFAULT_QUEUE_STEP)
        if step_data:
            data.update(step_data)

        row_frame = ctk.CTkFrame(
            self.queue_steps_frame,
            fg_color=BG_PANEL,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
        )
        row_frame.pack(fill="x", pady=(0, 6), padx=4)

        header = ctk.CTkFrame(row_frame, fg_color="transparent")
        header.pack(fill="x", padx=8, pady=(8, 4))

        index_label = ctk.CTkLabel(
            header,
            text="1",
            width=20,
            font=(FONT, 11, "bold"),
            text_color=ACCENT,
        )
        index_label.pack(side="left")

        type_var = tk.StringVar(value=data["type"])
        type_segment = ctk.CTkSegmentedButton(
            header,
            values=["Mouse", "Key"],
            width=120,
            height=26,
            font=(FONT, 9),
            fg_color=BG_INPUT,
            selected_color=ACCENT,
            selected_hover_color=ACCENT_DIM,
            unselected_color=BG_HOVER,
            unselected_hover_color=BG_INPUT,
            text_color=TEXT_PRI,
        )
        type_segment.set("Mouse" if data["type"] == "mouse" else "Key")
        type_segment.pack(side="left", padx=(6, 0))

        remove_btn = ctk.CTkButton(
            header,
            text="Remove",
            width=64,
            height=24,
            corner_radius=4,
            font=(FONT, 9),
            fg_color=BG_HOVER,
            hover_color=DANGER_DIM,
            text_color=TEXT_SEC,
        )
        remove_btn.pack(side="right")

        body = ctk.CTkFrame(row_frame, fg_color="transparent")
        body.pack(fill="x", padx=8, pady=(0, 8))

        mouse_body = ctk.CTkFrame(body, fg_color="transparent")
        key_body = ctk.CTkFrame(body, fg_color="transparent")

        x_var = tk.StringVar(value=data["x"])
        y_var = tk.StringVar(value=data["y"])
        key_var = tk.StringVar(value=data["key"])
        delay_var = tk.StringVar(value=data["delay_after"])

        mouse_row = ctk.CTkFrame(mouse_body, fg_color="transparent")
        mouse_row.pack(fill="x")

        for col, (lbl, var) in enumerate((("X", x_var), ("Y", y_var))):
            ctk.CTkLabel(
                mouse_row,
                text=lbl,
                font=(FONT, 9),
                text_color=TEXT_SEC,
            ).grid(row=0, column=col * 2, sticky="w", padx=(0 if col == 0 else 8, 4))
            entry = ctk.CTkEntry(
                mouse_row,
                textvariable=var,
                width=60,
                height=28,
                corner_radius=6,
                font=(FONT, 11, "bold"),
                fg_color=BG_INPUT,
                border_color=BORDER,
                text_color=TEXT_PRI,
                justify="center",
            )
            entry.grid(row=0, column=col * 2 + 1, sticky="w")
            self._bind_numeric_entry(entry, "signed_int")

        pick_btn = ctk.CTkButton(
            mouse_row,
            text="Pick",
            width=52,
            height=28,
            corner_radius=6,
            font=(FONT, 9),
            fg_color=BG_HOVER,
            hover_color=BG_INPUT,
            text_color=ACCENT,
        )
        pick_btn.grid(row=0, column=4, padx=(8, 0))

        key_row = ctk.CTkFrame(key_body, fg_color="transparent")
        key_row.pack(fill="x")
        key_row.grid_columnconfigure(0, weight=1)

        key_entry = ctk.CTkEntry(
            key_row,
            textvariable=key_var,
            height=28,
            corner_radius=6,
            font=(FONT, 12, "bold"),
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRI,
            placeholder_text="e.g. b, enter, space",
            placeholder_text_color=TEXT_SEC,
        )
        key_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        capture_btn = ctk.CTkButton(
            key_row,
            text="Capture",
            width=72,
            height=28,
            corner_radius=6,
            font=(FONT, 9),
            fg_color=BG_HOVER,
            hover_color=BG_INPUT,
            text_color=ACCENT,
        )
        capture_btn.grid(row=0, column=1)

        wait_row = ctk.CTkFrame(body, fg_color="transparent")
        wait_row.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(
            wait_row,
            text="Then wait",
            font=(FONT, 9),
            text_color=TEXT_SEC,
        ).pack(side="left")

        delay_entry = ctk.CTkEntry(
            wait_row,
            textvariable=delay_var,
            width=52,
            height=28,
            corner_radius=6,
            font=(FONT, 11, "bold"),
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRI,
            justify="center",
        )
        delay_entry.pack(side="left", padx=(6, 0))
        self._bind_numeric_entry(delay_entry, "decimal")

        ctk.CTkLabel(
            wait_row,
            text="sec before next step",
            font=(FONT, 9),
            text_color=TEXT_SEC,
        ).pack(side="left", padx=(6, 0), pady=5)

        row_ref: dict = {
            "frame": row_frame,
            "index_label": index_label,
            "type_var": type_var,
            "type_segment": type_segment,
            "mouse_body": mouse_body,
            "key_body": key_body,
            "x_var": x_var,
            "y_var": y_var,
            "key_var": key_var,
            "delay_var": delay_var,
            "pick_btn": pick_btn,
            "capture_btn": capture_btn,
            "key_entry": key_entry,
            "remove_btn": remove_btn,
        }
        self._queue_rows.append(row_ref)
        row_index = len(self._queue_rows) - 1

        def refresh_type(*_):
            is_mouse = type_var.get() == "mouse"
            type_segment.set("Mouse" if is_mouse else "Key")
            if is_mouse:
                key_body.pack_forget()
                mouse_body.pack(fill="x")
            else:
                mouse_body.pack_forget()
                key_body.pack(fill="x")
            self._update_hotkey_hint()
            self._refresh_geometry()

        def on_type_segment(label):
            type_var.set("mouse" if label == "Mouse" else "key")
            refresh_type()

        type_segment.configure(command=on_type_segment)
        type_var.trace_add("write", refresh_type)

        pick_btn.configure(command=lambda i=row_index: self._queue_capture_position(i))
        capture_btn.configure(command=lambda i=row_index: self._queue_capture_key(i))
        remove_btn.configure(command=lambda i=row_index: self._queue_remove_step(i))

        refresh_type()
        self._queue_renumber()
        self._refresh_geometry()

    def _queue_remove_step(self, index: int):
        if self._is_running or index < 0 or index >= len(self._queue_rows):
            return
        if len(self._queue_rows) <= 1:
            messagebox.showinfo("Action queue", "Keep at least one step in the queue.")
            return
        row = self._queue_rows.pop(index)
        row["frame"].destroy()
        self._rebind_queue_row_callbacks()
        self._queue_renumber()
        self._refresh_geometry()

    def _rebind_queue_row_callbacks(self):
        for index, row in enumerate(self._queue_rows):
            row["pick_btn"].configure(command=lambda i=index: self._queue_capture_position(i))
            row["capture_btn"].configure(command=lambda i=index: self._queue_capture_key(i))
            row["remove_btn"].configure(command=lambda i=index: self._queue_remove_step(i))

    def _queue_clear_ui(self):
        for row in self._queue_rows:
            row["frame"].destroy()
        self._queue_rows.clear()

    def _queue_load_steps(self, steps: list[dict[str, str]]):
        self._queue_clear_ui()
        if steps:
            for step in steps:
                self._queue_add_step(step)
        else:
            self._queue_add_step()
        self._queue_renumber()

    def _queue_capture_position(self, index: int):
        if self._is_running:
            return
        self._queue_pick_index = index
        self._capture_mouse_position()

    def _queue_capture_key(self, index: int):
        if self._is_running:
            return
        self._queue_key_capture_index = index
        self._capture_key()

    def _toggle_fixed_position(self):
        mode = "coords" if self.fixed_pos_var.get() else "free"
        self._select_mouse_mode(mode)
        self._refresh_geometry()

    def _select_mouse_mode(self, mode):
        self.mouse_click_mode = mode
        if mode == "coords":
            self.coords_frame.pack(fill="x", pady=(8, 0))
            if hasattr(self, "fixed_pos_var"):
                self.fixed_pos_var.set(True)
        else:
            self.coords_frame.pack_forget()
            if hasattr(self, "fixed_pos_var"):
                self.fixed_pos_var.set(False)

    def _select_action(self, action):
        self.action_type = action
        label = "Mouse" if action == "mouse" else "Key"
        if hasattr(self, "action_segment"):
            self.action_segment.set(label)
        if action == "mouse":
            self.key_panel.pack_forget()
            self.mouse_panel.pack(fill="x")
            if self.mouse_click_mode == "coords":
                self.coords_frame.pack(fill="x", pady=(8, 0))
            else:
                self.coords_frame.pack_forget()
        else:
            self.mouse_panel.pack_forget()
            self.key_panel.pack(fill="x")
        self._update_key_section_state()
        self._update_hotkey_hint()
        self._refresh_geometry()

    def _update_key_section_state(self):
        if not hasattr(self, "key_entry"):
            return
        if self.automation_mode == "queue":
            self.key_entry.configure(state="disabled")
            self.capture_key_btn.configure(state="disabled")
            steps = self._queue_snapshot() if self._queue_rows else []
            if queue_uses_f7(steps):
                self.hotkey_label.configure(text_color=WARN)
            else:
                self.hotkey_label.configure(text_color=TEXT_SEC)
            return
        if self.action_type == "mouse":
            self.key_entry.configure(state="disabled")
            self.capture_key_btn.configure(state="disabled")
            self.hotkey_label.configure(text_color=TEXT_SEC)
        else:
            self.key_entry.configure(state="normal")
            if not self._key_capture_active:
                self.capture_key_btn.configure(state="normal")
            key = self.key_var.get().strip().lower()
            if key == "f7":
                self.hotkey_label.configure(text_color=WARN)
            else:
                self.hotkey_label.configure(text_color=TEXT_SEC)

    def _on_key_changed(self):
        key = self.key_var.get().strip().lower()
        became_f7 = key == "f7" and self._last_key != "f7"
        self._last_key = key
        self._update_key_section_state()
        self._update_hotkey_hint(notify_f7=became_f7)

    def _get_force_stop_key(self):
        if self.automation_mode == "queue":
            steps = self._queue_snapshot() if self._queue_rows else []
            if queue_uses_f7(steps):
                return ALT_FORCE_STOP
            return DEFAULT_FORCE_STOP
        if (
            self.action_type == "key"
            and hasattr(self, "key_var")
            and self.key_var.get().strip().lower() == "f7"
        ):
            return ALT_FORCE_STOP
        return DEFAULT_FORCE_STOP

    def _update_hotkey_hint(self, notify_f7=False):
        if not hasattr(self, "hotkey_var"):
            return

        stop_key = self._get_force_stop_key().upper()
        key = self.key_var.get().strip().lower() if hasattr(self, "key_var") else ""

        if self.automation_mode == "queue":
            steps = self._queue_snapshot() if self._queue_rows else []
            if queue_uses_f7(steps):
                text = f"Emergency stop: {stop_key} (F7 is in the queue)"
                if hasattr(self, "hotkey_label"):
                    self.hotkey_label.configure(text_color=WARN)
            else:
                text = f"Emergency stop: {stop_key}"
                if hasattr(self, "hotkey_label"):
                    self.hotkey_label.configure(text_color=TEXT_SEC)
            self.hotkey_var.set(text)
            return

        if self.action_type == "key" and key == "f7":
            text = f"Emergency stop: {stop_key} (F7 is in use)"
            if hasattr(self, "hotkey_label"):
                self.hotkey_label.configure(text_color=WARN)
            if notify_f7:
                messagebox.showinfo(
                    "Emergency stop adjusted",
                    "You selected F7 as the automation key.\n\n"
                    "Emergency stop will use F8 to avoid a conflict.",
                )
        else:
            text = f"Emergency stop: {stop_key}"
            if hasattr(self, "hotkey_label"):
                self.hotkey_label.configure(text_color=TEXT_SEC)

        self.hotkey_var.set(text)

    def _select_key_entry(self):
        if self.action_type == "key":
            self.key_entry.select_range(0, "end")
            self.key_entry.icursor("end")

    # --- Timing panel ---

    def _build_timing_card(self, parent):
        _, content = self._card(parent, "Timing")

        interval_row = ctk.CTkFrame(content, fg_color="transparent")
        interval_row.pack(fill="x", anchor="w")

        self.interval_var = tk.StringVar(value="1.0")
        self.interval_var.trace_add("write", lambda *_: self._sync_preset_highlight())

        self._pack_inline_label(interval_row, "Interval", padx=(0, 8))

        self.interval_entry = ctk.CTkEntry(
            interval_row,
            textvariable=self.interval_var,
            width=64,
            height=CONTROL_H,
            corner_radius=6,
            font=(FONT, 14, "bold"),
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRI,
            justify="center",
        )
        self.interval_entry.pack(side="left")
        self._bind_numeric_entry(self.interval_entry, "decimal")

        self._pack_inline_label(interval_row, "seconds", padx=(8, 0))

        self.interval_hint_var = tk.StringVar(value="")
        self.interval_hint_label = ctk.CTkLabel(
            content,
            textvariable=self.interval_hint_var,
            font=(FONT, 9),
            text_color=TEXT_SEC,
            wraplength=400,
            justify="left",
        )
        self.interval_hint_label.pack(anchor="w", pady=(4, 0))
        self._update_interval_hint()

        presets = ctk.CTkFrame(content, fg_color="transparent")
        presets.pack(fill="x", anchor="w", pady=(8, 0))

        self._preset_buttons = {}
        for i, (label, val) in enumerate(INTERVAL_PRESETS):
            btn = ctk.CTkButton(
                presets,
                text=label,
                width=44,
                height=24,
                corner_radius=4,
                font=(FONT, 9),
                fg_color=BG_INPUT,
                hover_color=BG_HOVER,
                text_color=TEXT_SEC,
                command=lambda v=val: self._set_interval_preset(v),
            )
            btn.pack(side="left", padx=(0 if i == 0 else 4, 0))
            self._preset_buttons[val] = btn

        repeat_row = ctk.CTkFrame(content, fg_color="transparent")
        repeat_row.pack(fill="x", anchor="w", pady=(12, 0))

        self.repeat_var = tk.BooleanVar(value=False)
        self.repeat_checkbox = ctk.CTkCheckBox(
            repeat_row,
            text="Limit repetitions",
            variable=self.repeat_var,
            font=(FONT, 10),
            text_color=TEXT_PRI,
            fg_color=ACCENT,
            hover_color=ACCENT_DIM,
            border_color=BORDER,
            checkbox_width=16,
            checkbox_height=16,
            checkmark_color=TEXT_PRI,
            command=self._toggle_repeat,
        )
        self.repeat_checkbox.pack(side="left")

        self.repeat_count_var = tk.StringVar(value="10")
        self.repeat_count_entry = ctk.CTkEntry(
            repeat_row,
            textvariable=self.repeat_count_var,
            width=56,
            height=CONTROL_H,
            corner_radius=6,
            font=(FONT, 13, "bold"),
            fg_color=BG_INPUT,
            border_color=BORDER,
            text_color=TEXT_PRI,
            justify="center",
        )
        self._bind_numeric_entry(self.repeat_count_entry, "unsigned_int")

        self.repeat_times_label = ctk.CTkLabel(
            repeat_row,
            text="times",
            font=(FONT, 10),
            text_color=TEXT_SEC,
        )

        self._toggle_repeat()
        self._sync_preset_highlight()

    def _update_interval_hint(self):
        if not hasattr(self, "interval_hint_var"):
            return
        if getattr(self, "automation_mode", "single") == "queue":
            self.interval_hint_var.set(
                "Cycle interval: pause after the full queue finishes before it runs again."
            )
            if hasattr(self, "repeat_checkbox"):
                self.repeat_checkbox.configure(text="Limit queue cycles")
        else:
            self.interval_hint_var.set("Time between each repeated action.")
            if hasattr(self, "repeat_checkbox"):
                self.repeat_checkbox.configure(text="Limit repetitions")

    def _set_interval_preset(self, value):
        self.interval_var.set(str(value))

    def _sync_preset_highlight(self):
        if not self._preset_buttons:
            return
        try:
            current = float(self.interval_var.get().replace(",", "."))
        except (ValueError, tk.TclError):
            current = None
        for val, btn in self._preset_buttons.items():
            if current is not None and abs(current - val) < 0.001:
                btn.configure(fg_color=ACCENT, hover_color=ACCENT_DIM, text_color=TEXT_PRI)
            else:
                btn.configure(fg_color=BG_INPUT, hover_color=BG_HOVER, text_color=TEXT_SEC)

    def _toggle_repeat(self):
        if self.repeat_var.get():
            self.repeat_count_entry.pack(side="left", padx=(8, 0))
            self.repeat_times_label.pack(side="left", padx=(8, 0), pady=7)
        else:
            self.repeat_count_entry.pack_forget()
            self.repeat_times_label.pack_forget()
        self._refresh_geometry()

    # --- Settings persistence ---

    def _load_persisted_settings(self):
        data = load_settings()

        mode = data.get("automation_mode", "single")
        if mode not in ("single", "queue"):
            mode = "single"

        action = data.get("action_type", "mouse")
        if action not in ("mouse", "key"):
            action = "mouse"

        mouse_mode = data.get("mouse_click_mode", "free")
        if mouse_mode not in ("free", "coords"):
            mouse_mode = "free"

        self.click_x_var.set(str(data.get("click_x", "0")))
        self.click_y_var.set(str(data.get("click_y", "0")))

        key = str(data.get("key", "space"))
        self._last_key = key.strip().lower()
        self.key_var.set(key)

        self.interval_var.set(str(data.get("interval", "1.0")))
        self.repeat_var.set(bool(data.get("repeat", False)))
        self.repeat_count_var.set(str(data.get("repeat_count", "10")))

        self._toggle_repeat()
        self.mouse_click_mode = mouse_mode
        self._select_action(action)
        self._select_mouse_mode(mouse_mode)
        self._queue_load_steps(normalize_queue(data.get("action_queue", [])))
        self._select_automation_mode(mode)
        self._sync_preset_highlight()
        self._update_hotkey_hint()

    def _save_persisted_settings(self):
        payload = {
            "automation_mode": self.automation_mode,
            "action_type": self.action_type,
            "mouse_click_mode": self.mouse_click_mode,
            "click_x": self.click_x_var.get(),
            "click_y": self.click_y_var.get(),
            "key": self.key_var.get(),
            "interval": self.interval_var.get(),
            "repeat": self.repeat_var.get(),
            "repeat_count": self.repeat_count_var.get(),
            "action_queue": self._queue_snapshot() if self._queue_rows else [],
        }
        save_settings(payload)

    # --- Emergency stop listener ---

    def _normalize_key_name(self, key):
        try:
            if key.char:
                return key.char.lower()
        except AttributeError:
            pass
        return str(key).replace("Key.", "").replace("_l", "").replace("_r", "").lower().replace("_", " ")

    def _start_force_stop_listener(self):
        self._stop_force_stop_listener()
        if not PYNPUT_AVAILABLE:
            return

        stop_key = self._get_force_stop_key()

        def on_press(key):
            if self._normalize_key_name(key) == stop_key:
                self.after(0, self._force_stop)
            return self._is_running

        self._stop_listener = keyboard.Listener(on_press=on_press)
        self._stop_listener.daemon = True
        self._stop_listener.start()

    def _stop_force_stop_listener(self):
        if self._stop_listener is not None:
            try:
                self._stop_listener.stop()
            except Exception:
                pass
            self._stop_listener = None

    def _force_stop(self):
        if self._is_running:
            stop_key = self._get_force_stop_key().upper()
            self.clicker.stop()
            self.status_var.set(f"Stopped (emergency stop via {stop_key})")
            self.tick_var.set("")
            self._set_running_ui(False)
            self._stop_force_stop_listener()

    # --- Input capture ---

    def _capture_key(self):
        if not PYNPUT_AVAILABLE:
            messagebox.showerror("Error", "pynput library not found.")
            return
        if self._key_capture_active:
            return

        self._key_capture_active = True
        self.capture_key_btn.configure(state="disabled")
        self.status_var.set("Press any key…")

        def on_press(key):
            try:
                captured = key.char
            except AttributeError:
                captured = str(key).replace("Key.", "").replace("_l", "").replace("_r", "").replace("_", " ")
            self.after(0, lambda: self._finish_key_capture(captured))
            return False

        self._key_capture_listener = keyboard.Listener(on_press=on_press)
        self._key_capture_listener.daemon = True
        self._key_capture_listener.start()

    def _finish_key_capture(self, captured):
        self._key_capture_active = False
        if self._key_capture_listener is not None:
            try:
                self._key_capture_listener.stop()
            except Exception:
                pass
            self._key_capture_listener = None

        if captured:
            key = captured.lower()
            if self._queue_key_capture_index is not None and 0 <= self._queue_key_capture_index < len(self._queue_rows):
                row = self._queue_rows[self._queue_key_capture_index]
                row["key_var"].set(key)
                row["type_var"].set("key")
                self._queue_key_capture_index = None
                self.status_var.set(f"Queue step key captured: '{captured}'")
                self._update_hotkey_hint()
                return

            became_f7 = key == "f7" and self._last_key != "f7"
            self._last_key = key
            self.key_var.set(key)
            if became_f7:
                messagebox.showinfo(
                    "Emergency stop adjusted",
                    "You selected F7 as the automation key.\n\n"
                    "Emergency stop will use F8 to avoid a conflict.",
                )
            self.status_var.set(f"Key captured: '{captured}'")
            self._update_hotkey_hint()
        else:
            self.status_var.set("No key captured.")
            self._queue_key_capture_index = None

        self._update_key_section_state()

    def _capture_mouse_position(self):
        if not PYNPUT_AVAILABLE:
            messagebox.showerror("Error", "pynput library not found.")
            return

        if self._coord_pick_active:
            self._cancel_coord_pick()
            return

        self._coord_pick_active = True
        self.withdraw()

        self._coord_coords_var = tk.StringVar(value="X: 0  Y: 0")
        self._coord_tooltip = ctk.CTkToplevel(self)
        self._coord_tooltip.overrideredirect(True)
        self._coord_tooltip.attributes("-topmost", True)
        self._coord_tooltip.configure(fg_color=BG_PANEL)

        border = ctk.CTkFrame(
            self._coord_tooltip,
            fg_color=BORDER,
            corner_radius=8,
            border_width=0,
        )
        border.pack(padx=1, pady=1)

        inner = ctk.CTkFrame(border, fg_color=BG_PANEL, corner_radius=7)
        inner.pack(padx=1, pady=1)

        content = ctk.CTkFrame(inner, fg_color="transparent")
        content.pack(padx=12, pady=10)

        ctk.CTkLabel(
            content,
            text="Click to set position",
            font=(FONT, 9),
            text_color=TEXT_SEC,
        ).pack(anchor="w")

        ctk.CTkLabel(
            content,
            text="Esc to cancel",
            font=(FONT, 8),
            text_color=TEXT_SEC,
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkLabel(
            content,
            textvariable=self._coord_coords_var,
            font=(FONT, 11, "bold"),
            text_color=TEXT_PRI,
        ).pack(anchor="w", pady=(6, 0))

        self._coord_tooltip.update_idletasks()

        def on_move(x, y):
            if self._coord_pick_active:
                self.after(0, lambda: self._update_coord_tooltip(x, y))

        def on_click(x, y, button, pressed):
            if pressed and button == Button.left and self._coord_pick_active:
                self.after(0, lambda: self._finish_coord_pick(x, y))
                return False
            return self._coord_pick_active

        def on_press(key):
            if key == Key.esc and self._coord_pick_active:
                self.after(0, self._cancel_coord_pick)
                return False
            return self._coord_pick_active

        self._coord_mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
        self._coord_kb_listener = keyboard.Listener(on_press=on_press)
        self._coord_mouse_listener.daemon = True
        self._coord_kb_listener.daemon = True
        self._coord_mouse_listener.start()
        self._coord_kb_listener.start()

        x, y = mouse_controller.position
        self._update_coord_tooltip(x, y)

    def _update_coord_tooltip(self, x, y):
        if not self._coord_pick_active or self._coord_tooltip is None:
            return
        self._coord_coords_var.set(f"X: {int(x)}  Y: {int(y)}")
        self._coord_tooltip.geometry(f"+{int(x) + 16}+{int(y) + 20}")

    def _finish_coord_pick(self, x, y):
        ix, iy = int(x), int(y)
        if self._queue_pick_index is not None and 0 <= self._queue_pick_index < len(self._queue_rows):
            row = self._queue_rows[self._queue_pick_index]
            row["x_var"].set(str(ix))
            row["y_var"].set(str(iy))
            row["type_var"].set("mouse")
            self._queue_pick_index = None
            self._cleanup_coord_pick()
            self.deiconify()
            self.lift()
            self.status_var.set(f"Queue step position captured: X={ix}, Y={iy}")
            return

        self.click_x_var.set(str(ix))
        self.click_y_var.set(str(iy))
        self._cleanup_coord_pick()
        self.deiconify()
        self.lift()
        self.status_var.set(f"Position captured: X={ix}, Y={iy}")
        min_x, min_y, max_x, max_y = get_virtual_screen_bounds()
        if ix < min_x or ix > max_x or iy < min_y or iy > max_y:
            self.status_var.set(
                f"Position captured ({ix}, {iy}) — outside detected bounds; check your monitors."
            )

    def _cancel_coord_pick(self):
        self._queue_pick_index = None
        self._cleanup_coord_pick()
        self.deiconify()
        self.lift()
        self.status_var.set("Position capture cancelled (Esc).")

    def _cleanup_coord_pick(self):
        self._coord_pick_active = False
        if self._coord_mouse_listener is not None:
            try:
                self._coord_mouse_listener.stop()
            except Exception:
                pass
            self._coord_mouse_listener = None
        if self._coord_kb_listener is not None:
            try:
                self._coord_kb_listener.stop()
            except Exception:
                pass
            self._coord_kb_listener = None
        if self._coord_tooltip is not None:
            try:
                self._coord_tooltip.destroy()
            except Exception:
                pass
            self._coord_tooltip = None

    def _parse_click_coordinates(self):
        try:
            x = int(self.click_x_var.get().strip())
            y = int(self.click_y_var.get().strip())
        except (ValueError, tk.TclError):
            messagebox.showwarning("Warning", "Enter valid X and Y coordinates (integers).")
            return None

        min_x, min_y, max_x, max_y = get_virtual_screen_bounds()
        if x < min_x or x > max_x or y < min_y or y > max_y:
            if not messagebox.askyesno(
                "Coordinate out of bounds",
                f"({x}, {y}) is outside the detected virtual desktop "
                f"(X: {min_x}..{max_x}, Y: {min_y}..{max_y}).\n\n"
                "This can happen if a monitor was disconnected or detection failed.\n"
                "Start anyway?",
            ):
                return None
        return x, y

    # --- Automation control ---

    def _set_queue_editing_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        if hasattr(self, "mode_segment"):
            self.mode_segment.configure(state=state)
        if hasattr(self, "queue_add_btn"):
            self.queue_add_btn.configure(state=state if len(self._queue_rows) < MAX_QUEUE_SIZE else "disabled")
        for row in self._queue_rows:
            row["type_segment"].configure(state=state)
            row["pick_btn"].configure(state=state)
            row["capture_btn"].configure(state=state)
            row["remove_btn"].configure(state=state)

    def _set_running_ui(self, running):
        self._is_running = running
        if running:
            self.state_dot.configure(fg_color=SUCCESS)
            self.state_label.configure(text="Running", text_color=SUCCESS)
            self.status_label.configure(text_color=SUCCESS)
            self.tick_label.configure(text_color=SUCCESS)
            self.action_btn.configure(
                text="Stop(F7/F8)",
                fg_color=DANGER,
                hover_color=DANGER_DIM,
                command=self._stop,
            )
            self._set_queue_editing_enabled(False)
        else:
            self.state_dot.configure(fg_color=TEXT_SEC)
            self.state_label.configure(text="Idle", text_color=TEXT_SEC)
            self.status_label.configure(text_color=TEXT_SEC)
            self.tick_label.configure(text_color=TEXT_SEC)
            self.action_btn.configure(
                text="Start",
                fg_color=ACCENT,
                hover_color=ACCENT_DIM,
                command=self._start,
            )
            self._set_queue_editing_enabled(True)
            self._queue_renumber()

    def _start(self):
        if not PYNPUT_AVAILABLE:
            messagebox.showerror(
                "Error",
                "pynput library not found.\nInstall with: pip install pynput",
            )
            return

        try:
            interval = float(self.interval_var.get().replace(",", "."))
            if interval < 0.05:
                messagebox.showwarning("Warning", "Minimum interval is 0.05 seconds.")
                return
        except (ValueError, tk.TclError):
            messagebox.showwarning("Warning", "Invalid interval.")
            return

        repeat = self.repeat_var.get()
        try:
            count = int(self.repeat_count_var.get()) if repeat else 0
            if repeat and count < 1:
                messagebox.showwarning("Warning", "Repeat count must be at least 1.")
                return
        except (ValueError, tk.TclError):
            messagebox.showwarning("Warning", "Invalid repeat count.")
            return

        if self.automation_mode == "queue":
            steps = self._queue_snapshot()
            error = validate_queue(steps)
            if error:
                messagebox.showwarning("Action queue", error)
                return

            step_count = len(steps)
            self.status_var.set(
                f"Running: queue ({step_count} steps) every {interval}s cycle"
            )
            self.tick_var.set("Cycle 0")
            self._set_running_ui(True)
            self._start_force_stop_listener()
            self._save_persisted_settings()

            self.clicker.start_queue(
                steps=steps,
                cycle_interval=interval,
                repeat=repeat,
                repeat_count=count,
                on_tick=self._on_queue_tick,
                on_done=self._on_done,
            )
            return

        action = self.action_type
        key = self.key_var.get().strip().lower()
        mouse_mode = "free"
        click_x, click_y = 0, 0

        if action == "mouse" and self.mouse_click_mode == "coords":
            coords = self._parse_click_coordinates()
            if coords is None:
                return
            click_x, click_y = coords
            mouse_mode = "coords"

        if action == "key":
            if not key:
                messagebox.showwarning("Warning", "Enter a key before starting.")
                return
            if len(key) > 1 and key not in SPECIAL_KEYS:
                messagebox.showwarning(
                    "Invalid key",
                    f"'{key}' is not a recognized special key.\n\n"
                    "Use names like: enter, space, tab, f1, up, ctrl, delete, etc.",
                )
                return

        stop_key = self._get_force_stop_key().upper()
        if action == "mouse":
            if mouse_mode == "coords":
                label = f"mouse at ({click_x}, {click_y})"
            else:
                label = "mouse (current cursor position)"
        else:
            label = f"key '{key}'"
        self.status_var.set(f"Running: {label} every {interval}s")
        self.tick_var.set("0 actions")
        self._set_running_ui(True)
        self._start_force_stop_listener()
        self._save_persisted_settings()

        self.clicker.start(
            action_type=action,
            key_value=key,
            interval=interval,
            repeat=repeat,
            repeat_count=count,
            on_tick=self._on_tick,
            on_done=self._on_done,
            mouse_mode=mouse_mode,
            click_x=click_x,
            click_y=click_y,
        )

    def _stop(self):
        self.clicker.stop()
        self._stop_force_stop_listener()
        self.status_var.set("Stopped")
        self.tick_var.set("")
        self._set_running_ui(False)

    def _on_tick(self, count):
        self.after(0, lambda: self.tick_var.set(f"{count} actions"))

    def _on_queue_tick(self, cycle: int, step: int, total_steps: int):
        self.after(
            0,
            lambda: self.tick_var.set(f"Cycle {cycle} · Step {step}/{total_steps}"),
        )

    def _on_done(self):
        self.after(0, self._stop)
