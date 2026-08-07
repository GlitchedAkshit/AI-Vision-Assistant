import customtkinter as ctk
from PIL import Image
import theme

class CameraFrame(ctk.CTkFrame):
    """Displays the live annotated camera feed streamed from AssistantWorker."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS, **kwargs)

        self._label = ctk.CTkLabel(
            self, text="Starting camera...", text_color=theme.TEXT_SECONDARY
        )
        self._label.pack(expand=True, fill="both", padx=8, pady=8)

        self._image_ref = None

    def update_frame(self, rgb_array):
        if rgb_array is None:
            return

        pil_image = Image.fromarray(rgb_array)
        w, h = pil_image.size

        ctk_image = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(w, h))
        self._image_ref = ctk_image
        self._label.configure(image=ctk_image, text="")
