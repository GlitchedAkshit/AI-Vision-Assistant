"""
Optional offline text-to-speech feedback (e.g. "Volume up", "Mouse Paused") so you don't have to watch the screen to know an action fired.

Runs the TTS engine on a background thread so it never blocks the camera
loop.
"""

import queue
import threading

try:
    import pyttsx3
    _TTS_AVAILABLE = True
except ImportError:
    _TTS_AVAILABLE = False


class VoiceFeedback:
    def __init__(self, enabled=True):
        self.enabled = enabled and _TTS_AVAILABLE
        self._queue = queue.Queue()
        self._engine = None
        self._thread = None

        if self.enabled:
            try:
                self._engine = pyttsx3.init()
                self._thread = threading.Thread(target=self._worker, daemon=True)
                self._thread.start()
            except Exception as e:
                print(f"[voice_feedback] Could not initialize TTS engine: {e}")
                self.enabled = False
        elif enabled and not _TTS_AVAILABLE:
            print("[voice_feedback] pyttsx3 not installed - voice feedback disabled. "
                  "Run: pip install pyttsx3")

    def _worker(self):
        while True:
            text = self._queue.get()
            if text is None:
                break
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as e:
                print(f"[voice_feedback] TTS error: {e}")

    def speak(self, text):
        if self.enabled:
            self._queue.put(text)
