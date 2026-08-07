import json
import tkinter as tk
from tkinter import messagebox

import config

FIELDS = [
    ("SMOOTHENING", "Mouse smoothing (higher = smoother, more lag)"),
    ("PINCH_THRESHOLD_RATIO", "Pinch sensitivity (lower = tighter pinch needed)"),
    ("DRAG_HOLD_TIME", "Pinch-hold time before it becomes a drag (sec)"),
    ("SCROLL_SPEED", "Scroll speed"),
    ("IDLE_TIMEOUT", "Auto-pause mouse after N idle seconds (0 = off)"),
    ("VOLUME_STEP", "Volume step per Thumbs Up/Down (0-1)"),
    ("BRIGHTNESS_STEP", "Brightness step per +/- key (0-100)"),
    ("EAR_CLOSED_THRESHOLD", "Eye-closed threshold for wink detection"),
    ("VOICE_FEEDBACK_ENABLED", "Voice feedback on action (True/False)"),
    ("SESSION_LOGGING_ENABLED", "Log session to CSV (True/False)"),
]


def load_existing():
    try:
        with open("settings.json") as f:
            return json.load(f)
    except Exception:
        return {}


def save(values):
    parsed = {}
    for key, raw in values.items():
        default = getattr(config, key)
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
            messagebox.showerror("Invalid value", f"'{raw}' is not valid for {key}")
            return False

    with open("settings.json", "w") as f:
        json.dump(parsed, f, indent=2)

    messagebox.showinfo("Saved", "Saved to settings.json - restart main.py to apply.")
    return True


def main():
    existing = load_existing()

    root = tk.Tk()
    root.title("AI Vision Assistant - Settings")
    root.configure(bg="#1e1e1e")

    entries = {}

    for row, (key, label) in enumerate(FIELDS):
        tk.Label(root, text=label, bg="#1e1e1e", fg="white", anchor="w").grid(
            row=row, column=0, sticky="w", padx=10, pady=6
        )
        entry = tk.Entry(root, width=12)
        default_value = existing.get(key, getattr(config, key))
        entry.insert(0, str(default_value))
        entry.grid(row=row, column=1, padx=10, pady=6)
        entries[key] = entry

    def on_save():
        values = {key: entry.get() for key, entry in entries.items()}
        save(values)

    tk.Button(root, text="Save", command=on_save, bg="#2e7d32", fg="white").grid(
        row=len(FIELDS), column=0, columnspan=2, pady=12
    )

    root.mainloop()


if __name__ == "__main__":
    main()
