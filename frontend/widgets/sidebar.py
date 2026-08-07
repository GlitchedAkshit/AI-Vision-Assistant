import os
import customtkinter as ctk
from PIL import Image
import theme
from .nav_button import NavButton

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")


class Sidebar(ctk.CTkFrame):
    """Left navigation rail: logo + page links."""

    PAGES = [
        ("Dashboard", "dashboard"),
        ("Settings", "settings"),
        ("Logs", "logs"),
        ("About", "about"),
    ]

    def __init__(self, master, on_navigate, **kwargs):
        super().__init__(
            master, width=theme.SIDEBAR_WIDTH, fg_color=theme.BG_SIDEBAR,
            corner_radius=0, **kwargs
        )
        self.grid_propagate(False)

        self._on_navigate = on_navigate
        self._buttons = {}

        self._build_logo()

        for label, icon_name in self.PAGES:
            btn = NavButton(self, text=label, icon_name=icon_name,
                             command=lambda p=label: self._select(p))
            btn.pack(fill="x", padx=14, pady=4)
            self._buttons[label] = btn

        self._select("Dashboard")

    def _build_logo(self):
        logo_path = os.path.join(ASSETS_DIR, "logo.png")
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=14, pady=(20, 24))

        if os.path.exists(logo_path):
            pil_image = Image.open(logo_path)
            ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(36, 36))
            ctk.CTkLabel(frame, image=ctk_image, text="").pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            frame, text="AI Vision\nAssistant", font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY, justify="left"
        ).pack(side="left")

    def _select(self, page):
        for name, btn in self._buttons.items():
            btn.set_active(name == page)
        self._on_navigate(page)
