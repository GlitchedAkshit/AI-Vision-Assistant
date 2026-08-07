import customtkinter as ctk
import theme


class StatCard(ctk.CTkFrame):
    """Small labeled value card used on the dashboard (Gesture, FPS, etc.)."""

    def __init__(self, master, title, value="-", value_color=None, **kwargs):
        super().__init__(master, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS, **kwargs)

        self._title_label = ctk.CTkLabel(
            self, text=title, font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY, anchor="w"
        )
        self._title_label.pack(anchor="w", padx=12, pady=(10, 0))

        self._value_label = ctk.CTkLabel(
            self, text=str(value), font=theme.FONT_HEADING,
            text_color=value_color or theme.TEXT_PRIMARY, anchor="w"
        )
        self._value_label.pack(anchor="w", padx=12, pady=(0, 10))

    def set_value(self, value, color=None):
        self._value_label.configure(text=str(value))
        if color:
            self._value_label.configure(text_color=color)
