import os
import customtkinter as ctk

import theme

ICONS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "icons")


class NavButton(ctk.CTkButton):
    """Sidebar navigation button with an active/inactive visual state and
    an optional icon (looked up from assets/icons/<icon_name>.png)."""

    def __init__(self, master, text, command, icon_name=None, **kwargs):
        image = None
        icon_path = os.path.join(ICONS_DIR, f"{icon_name}.png") if icon_name else None

        if icon_path and os.path.exists(icon_path):
            from PIL import Image
            pil_img = Image.open(icon_path)
            image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(20, 20))

        super().__init__(
            master,
            text=f"  {text}",
            image=image,
            command=command,
            anchor="w",
            corner_radius=theme.RADIUS,
            fg_color="transparent",
            hover_color=theme.BG_CARD,
            text_color=theme.TEXT_SECONDARY,
            font=theme.FONT_BODY,
            height=42,
            **kwargs,
        )

    def set_active(self, active):
        if active:
            self.configure(fg_color=theme.BG_CARD, text_color=theme.TEXT_PRIMARY)
        else:
            self.configure(fg_color="transparent", text_color=theme.TEXT_SECONDARY)
