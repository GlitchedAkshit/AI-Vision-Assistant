import customtkinter as ctk
import theme

GESTURE_MAP = [
    ("Point (any pose)", "Move cursor"),
    ("Pinch", "Click - hold to drag"),
    ("Right Pinch (thumb+middle)", "Right click"),
    ("Scroll (3 fingers)", "Scroll up/down"),
    ("Thumbs Up / Down", "Volume up / down"),
    ("Fist / Open Palm", "Pause / Resume mouse"),
    ("Wink Left / Right", "Mute / Next track"),
    ("Nod / Shake head", "Play-pause / Previous track"),
]


class AboutPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self, text="AI Vision Assistant", font=theme.FONT_TITLE, text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w")
        ctk.CTkLabel(
            self, text="Hand-gesture mouse & system control, plus face and emotion detection.",
            font=theme.FONT_BODY, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", pady=(4, 20))

        card = ctk.CTkFrame(self, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS)
        card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            card, text="Gesture Map", font=theme.FONT_HEADING, text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w", padx=16, pady=(16, 8))

        for gesture, action in GESTURE_MAP:
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            ctk.CTkLabel(
                row, text=gesture, font=theme.FONT_BODY, text_color=theme.TEXT_PRIMARY,
                width=240, anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=action, font=theme.FONT_BODY, text_color=theme.ACCENT_YELLOW, anchor="w"
            ).pack(side="left")

        ctk.CTkLabel(
            card, text="Built with OpenCV + MediaPipe + CustomTkinter",
            font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY
        ).pack(anchor="w", padx=16, pady=(20, 16))
