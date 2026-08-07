import os
import sys
import customtkinter as ctk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
import system_control

import theme
from camera_frame import CameraFrame
from widgets.stat_card import StatCard


class DashboardPage(ctk.CTkFrame):
    """Live camera feed + gesture/face stats + quick-action controls."""

    def __init__(self, master, worker, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._worker = worker

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.camera_frame = CameraFrame(self)
        self.camera_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        side_panel = ctk.CTkFrame(self, fg_color="transparent")
        side_panel.grid(row=0, column=1, sticky="nsew")

        self.card_gesture = StatCard(side_panel, "Gesture")
        self.card_gesture.pack(fill="x", pady=(0, 10))

        self.card_confidence = StatCard(side_panel, "Confidence")
        self.card_confidence.pack(fill="x", pady=(0, 10))

        self.card_hands = StatCard(side_panel, "Hands Detected")
        self.card_hands.pack(fill="x", pady=(0, 10))

        self.card_mouse = StatCard(side_panel, "Mouse Mode")
        self.card_mouse.pack(fill="x", pady=(0, 10))

        self.card_face = StatCard(side_panel, "Emotion")
        self.card_face.pack(fill="x", pady=(0, 10))

        self.card_fps = StatCard(side_panel, "FPS")
        self.card_fps.pack(fill="x", pady=(0, 16))

        self._build_quick_actions(side_panel)

    def _build_quick_actions(self, parent):
        box = ctk.CTkFrame(parent, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        box.pack(fill="x")

        ctk.CTkLabel(
            box, text="Quick Actions", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self._pause_btn = ctk.CTkButton(
            box, text="Pause Mouse", command=self._toggle_mouse,
            fg_color=theme.ACCENT_RED, hover_color="#c62828"
        )
        self._pause_btn.pack(fill="x", padx=12, pady=6)

        def action_button(label, fn):
            ctk.CTkButton(
                box, text=label, command=fn, fg_color=theme.BG_SIDEBAR,
                hover_color=theme.BORDER
            ).pack(fill="x", padx=12, pady=4)

        action_button("File Explorer", system_control.open_file_explorer)
        action_button("Open Browser", system_control.open_browser)
        action_button("Play / Pause Media", system_control.play_pause)
        action_button("Lock PC", system_control.lock_pc)

        ctk.CTkFrame(box, height=6, fg_color="transparent").pack()

    def _toggle_mouse(self):
        state = self._worker.get_state()
        new_active = not state.get("mouse_active", True)
        self._worker.request_mouse_active(new_active)

    def refresh(self):
        """Called periodically by app.py to pull the latest frame/state."""
        frame = self._worker.get_frame()
        self.camera_frame.update_frame(frame)

        state = self._worker.get_state()

        self.card_gesture.set_value(state.get("gesture", "-"))
        self.card_confidence.set_value(f"{state.get('confidence', 0):.0f}%")
        self.card_hands.set_value(state.get("hand_count", 0))

        mouse_active = state.get("mouse_active", True)
        self.card_mouse.set_value(
            "Active" if mouse_active else "Paused",
            color=theme.ACCENT_GREEN if mouse_active else theme.ACCENT_RED,
        )
        self._pause_btn.configure(
            text="Pause Mouse" if mouse_active else "Resume Mouse",
            fg_color=theme.ACCENT_RED if mouse_active else theme.ACCENT_GREEN,
        )

        emotion = state.get("emotion", "-")
        emotion_conf = state.get("emotion_confidence", 0)
        self.card_face.set_value(f"{emotion} ({emotion_conf:.0f}%)" if emotion != "-" else "-")

        self.card_fps.set_value(state.get("fps", 0))
