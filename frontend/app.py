"""
Desktop frontend entry point.
    pip install -r ../requirements.txt
    pip install customtkinter
    python app.py
"""

import os
import sys
import customtkinter as ctk

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import theme
from widgets.sidebar import Sidebar
from dashboard import DashboardPage
from settings_page import SettingsPage
from logs_page import LogsPage
from about_page import AboutPage
from assistant_worker import AssistantWorker

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AI Vision Assistant")
        self.geometry("1366x768")
        self.minsize(950, 600)
        self.configure(fg_color=theme.BG_PRIMARY)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.worker = AssistantWorker()
        self.worker.start()

        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self._pages = {}
        self._build_pages()

        self.sidebar = Sidebar(self, on_navigate=self._show_page)
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self._show_page("Dashboard")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._tick()

    def _build_pages(self):
        self._pages = {
            "Dashboard": DashboardPage(self._content, self.worker),
            "Settings": SettingsPage(self._content, on_restart_worker=self._restart_worker),
            "Logs": LogsPage(self._content),
            "About": AboutPage(self._content),
        }
        for page in self._pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _show_page(self, name):
        page = self._pages.get(name)
        if page:
            page.lift()

    def _restart_worker(self):
        """Rebuilds the worker (and the pages that hold a reference to it)
        so settings.json changes actually take effect."""
        self.worker.stop()
        self.worker = AssistantWorker()
        self.worker.start()

        for page in self._pages.values():
            page.destroy()

        self._build_pages()
        self._show_page("Dashboard")
        

    def _tick(self):
        dashboard = self._pages.get("Dashboard")
        
        if dashboard:
            dashboard.refresh()
        self.after(33, self._tick)  # ~30 fps GUI refresh

    def _on_close(self):
        self.worker.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
