"""
Logs every gesture/emotion/head-gesture event fired during a session to a
timestamped CSV file, so you can review usage or debug misfires later.
"""

import csv
import os
from datetime import datetime

class SessionLogger:
    def __init__(self, enabled=True, log_dir="logs"):
        self.enabled = enabled
        self._file = None
        self._writer = None

        if not enabled:
            return

        try:
            os.makedirs(log_dir, exist_ok=True)
            filename = datetime.now().strftime("session_%Y%m%d_%H%M%S.csv")
            path = os.path.join(log_dir, filename)

            self._file = open(path, "w", newline="")
            self._writer = csv.writer(self._file)
            self._writer.writerow(["timestamp", "event_type", "detail"])
            print(f"[session_logger] Logging session to {path}")
        except Exception as e:
            print(f"[session_logger] Could not open log file: {e}")
            self.enabled = False

    def log(self, event_type, detail=""):
        if not self.enabled or self._writer is None:
            return
        self._writer.writerow([datetime.now().isoformat(timespec="seconds"), event_type, detail])
        self._file.flush()

    def close(self):
        if self._file:
            self._file.close()
