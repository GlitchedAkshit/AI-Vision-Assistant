import json
import os
import sys
import customtkinter as ctk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import config

import theme

FIELDS = [
    ("SMOOTHENING", "Mouse smoothing (higher = smoother, more lag)"),
    ("PINCH_THRESHOLD_RATIO", "Pinch sensitivity (lower = tighter pinch)"),
    ("DRAG_HOLD_TIME", "Pinch-hold time before drag starts (sec)"),
    ("SCROLL_SPEED", "Scroll speed"),
    ("IDLE_TIMEOUT", "Auto-pause mouse after N idle seconds (0 = off)"),
    ("VOLUME_STEP", "Volume step per Thumbs Up/Down (0-1)"),
    ("BRIGHTNESS_STEP", "Brightness step per action (0-100)"),
    ("EAR_CLOSED_RATIO", "Wink sensitivity (lower = easier to trigger)"),
    ("NOD_PITCH_RANGE_DEG", "Nod sensitivity (higher = requires a bigger nod)"),
    ("SHAKE_YAW_RANGE_DEG", "Shake sensitivity (higher = requires a bigger shake)"),
    ("VOICE_FEEDBACK_ENABLED", "Voice feedback on action (True/False)"),
    ("SESSION_LOGGING_ENABLED", "Log session to CSV (True/False)"),
]

SETTINGS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings.json"))


class SettingsPage(ctk.CTkFrame):
    """Editable form for the most commonly-tuned config.py values, saved to
    settings.json (picked up automatically by settings.apply_overrides())."""

    def __init__(self, master, on_restart_worker=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._on_restart_worker = on_restart_worker
        self._entries = {}

        ctk.CTkLabel(
            self, text="Settings", font=theme.FONT_TITLE, text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(
            self, text="Changes apply after restarting the assistant (button below).",
            font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(0, 16))

        scroll = ctk.CTkScrollableFrame(self, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        scroll.pack(fill="both", expand=True)

        existing = self._load_existing()

        for key, label in FIELDS:
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=8)

            ctk.CTkLabel(
                row, text=label, font=theme.FONT_BODY, text_color=theme.TEXT_PRIMARY, anchor="w"
            ).pack(side="left", fill="x", expand=True)

            entry = ctk.CTkEntry(row, width=100)
            entry.insert(0, str(existing.get(key, getattr(config, key, ""))))
            entry.pack(side="right")
            self._entries[key] = entry

        button_row = ctk.CTkFrame(self, fg_color="transparent")
        button_row.pack(fill="x", pady=12)

        ctk.CTkButton(
            button_row, text="Save", command=self._save,
            fg_color=theme.ACCENT_GREEN, hover_color="#00a844"
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            button_row, text="Save & Restart Assistant", command=self._save_and_restart,
            fg_color=theme.ACCENT_BLUE, hover_color="#1e88e5"
        ).pack(side="left")

        self._status_label = ctk.CTkLabel(
            self, text="", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        )
        self._status_label.pack(anchor="w", pady=(6, 0))

    def _load_existing(self):
        try:
            with open(SETTINGS_PATH) as f:
                return json.load(f)
        except Exception:
            return {}

    def _collect_values(self):
        parsed = {}
        for key, entry in self._entries.items():
            default = getattr(config, key, "")
            raw = entry.get()
            try:
                if isinstance(default, bool):
                    parsed[key] = raw.strip().lower() in ("1", "true", "yes", "on")
                elif isinstance(default, int):
                    parsed[key] = int(raw)
                elif isinstance(default, float):
                    parsed[key] = float(raw)
                else:
                    parsed[key] = raw
            except ValueError:
                self._status_label.configure(
                    text=f"Invalid value for {key}: '{raw}'", text_color=theme.ACCENT_RED
                )
                return None
        return parsed

    def _save(self):
        values = self._collect_values()
        if values is None:
            return
        with open(SETTINGS_PATH, "w") as f:
            json.dump(values, f, indent=2)
        self._status_label.configure(text="Saved settings.json", text_color=theme.ACCENT_GREEN)

    def _save_and_restart(self):
        values = self._collect_values()
        if values is None:
            return
        with open(SETTINGS_PATH, "w") as f:
            json.dump(values, f, indent=2)

        if self._on_restart_worker:
            self._on_restart_worker()
            self._status_label.configure(
                text="Saved and restarted assistant.", text_color=theme.ACCENT_GREEN
            )
        else:
            self._status_label.configure(text="Saved settings.json", text_color=theme.ACCENT_GREEN)
