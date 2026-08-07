import csv
import os
import customtkinter as ctk
import theme

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))


class LogsPage(ctk.CTkFrame):
    """Browse session log CSVs written by session_logger.py."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self, text="Session Logs", font=theme.FONT_TITLE, text_color=theme.TEXT_PRIMARY
        ).pack(anchor="w", pady=(0, 12))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        self._file_list = ctk.CTkScrollableFrame(
            body, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS, width=220
        )
        self._file_list.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self._text_box = ctk.CTkTextbox(
            body, fg_color=theme.BG_CARD, corner_radius=theme.RADIUS,
            font=theme.FONT_MONO, text_color=theme.TEXT_PRIMARY
        )
        self._text_box.grid(row=0, column=1, sticky="nsew")

        ctk.CTkButton(self, text="Refresh", command=self.refresh).pack(anchor="e", pady=(10, 0))

        self.refresh()

    def refresh(self):
        for widget in self._file_list.winfo_children():
            widget.destroy()

        self._text_box.delete("1.0", "end")

        files = []
        if os.path.isdir(LOG_DIR):
            files = sorted((f for f in os.listdir(LOG_DIR) if f.endswith(".csv")), reverse=True)

        if not files:
            ctk.CTkLabel(
                self._file_list, text="No logs yet", text_color=theme.TEXT_SECONDARY
            ).pack(pady=10)
            return

        for fname in files:
            ctk.CTkButton(
                self._file_list, text=fname, anchor="w", fg_color="transparent",
                hover_color=theme.BG_SIDEBAR, text_color=theme.TEXT_PRIMARY,
                command=lambda f=fname: self._show_file(f)
            ).pack(fill="x", padx=6, pady=2)

    def _show_file(self, filename):
        path = os.path.join(LOG_DIR, filename)
        self._text_box.delete("1.0", "end")

        try:
            with open(path, newline="") as f:
                rows = list(csv.reader(f))
        except Exception as e:
            self._text_box.insert("end", f"Could not read {filename}: {e}")
            return

        if not rows:
            self._text_box.insert("end", "(empty log)")
            return

        col_count = len(rows[0])
        widths = [
            max((len(str(r[i])) for r in rows if i < len(r)), default=0)
            for i in range(col_count)
        ]

        for row in rows:
            line = "  ".join(
                str(cell).ljust(widths[i]) for i, cell in enumerate(row) if i < len(widths)
            )
            self._text_box.insert("end", line + "\n")
