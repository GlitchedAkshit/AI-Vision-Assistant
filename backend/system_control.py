"""
Windows system-control actions: volume, brightness, screenshots, launching
apps, media keys, and locking the PC.

Each capability degrades gracefully - if an optional package isn't
installed, that specific feature prints a warning instead of crashing the
whole app.

Requires (Windows-only):
    pip install pycaw comtypes screen-brightness-control pyautogui
"""

import ctypes
import os
import subprocess
import webbrowser
from datetime import datetime

import pyautogui
import config

# ---------------------------------------------------------------------------
# Volume control (pycaw)
# ---------------------------------------------------------------------------
try:
    from pycaw.pycaw import AudioUtilities
    _PYCAW_AVAILABLE = True
except ImportError:
    _PYCAW_AVAILABLE = False

# Older pycaw releases (pre ~2024) required this lower-level path instead.
try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import IAudioEndpointVolume
    _PYCAW_LEGACY_AVAILABLE = True
except ImportError:
    _PYCAW_LEGACY_AVAILABLE = False


class VolumeControl:
    def __init__(self, step=None):
        self.step = step if step is not None else config.VOLUME_STEP
        self._volume = None  # IAudioEndpointVolume-like object

        if not _PYCAW_AVAILABLE:
            print("[system_control] pycaw not installed - volume control disabled. "
                  "Run: pip install pycaw comtypes")
            return

        try:
            device = AudioUtilities.GetSpeakers()

            if hasattr(device, "EndpointVolume"):
                # New pycaw API (~2024+): no Activate()/cast needed.
                self._volume = device.EndpointVolume
            elif _PYCAW_LEGACY_AVAILABLE:
                # Old pycaw API.
                interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self._volume = cast(interface, POINTER(IAudioEndpointVolume))
            else:
                print("[system_control] Unrecognized pycaw API version - volume control disabled.")
        except Exception as e:
            print(f"[system_control] Could not initialize volume control: {e}")

    def is_ready(self):
        return self._volume is not None

    def volume_up(self):
        if not self.is_ready():
            return
        current = self._volume.GetMasterVolumeLevelScalar()
        self._volume.SetMasterVolumeLevelScalar(min(1.0, current + self.step), None)

    def volume_down(self):
        if not self.is_ready():
            return
        current = self._volume.GetMasterVolumeLevelScalar()
        self._volume.SetMasterVolumeLevelScalar(max(0.0, current - self.step), None)

    def toggle_mute(self):
        if not self.is_ready():
            return None
        muted = bool(self._volume.GetMute())
        self._volume.SetMute(0 if muted else 1, None)
        return not muted

    def get_volume_percent(self):
        if not self.is_ready():
            return None
        return int(self._volume.GetMasterVolumeLevelScalar() * 100)


# ---------------------------------------------------------------------------
# Brightness control (screen-brightness-control)
# ---------------------------------------------------------------------------
try:
    import screen_brightness_control as sbc
    _SBC_AVAILABLE = True
except ImportError:
    _SBC_AVAILABLE = False


class BrightnessControl:
    def __init__(self, step=None):
        self.step = step if step is not None else config.BRIGHTNESS_STEP

        if not _SBC_AVAILABLE:
            print("[system_control] screen_brightness_control not installed - "
                  "brightness control disabled. Run: pip install screen-brightness-control")

    def is_ready(self):
        return _SBC_AVAILABLE

    def brightness_up(self):
        if not _SBC_AVAILABLE:
            return
        try:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(min(100, current + self.step))
        except Exception as e:
            print(f"[system_control] Brightness error: {e}")

    def brightness_down(self):
        if not _SBC_AVAILABLE:
            return
        try:
            current = sbc.get_brightness()[0]
            sbc.set_brightness(max(0, current - self.step))
        except Exception as e:
            print(f"[system_control] Brightness error: {e}")


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------
def take_screenshot():
    try:
        os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
        filename = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        path = os.path.join(config.SCREENSHOT_DIR, filename)
        pyautogui.screenshot(path)
        print(f"[system_control] Screenshot saved: {path}")
        return path
    except Exception as e:
        print(f"[system_control] Screenshot failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Launch apps
# ---------------------------------------------------------------------------
def open_file_explorer():
    try:
        subprocess.Popen("explorer")
    except Exception as e:
        print(f"[system_control] Could not open File Explorer: {e}")


def open_browser(url="https://www.google.com"):
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"[system_control] Could not open browser: {e}")


def open_notepad():
    try:
        subprocess.Popen("notepad.exe")
    except Exception as e:
        print(f"[system_control] Could not open Notepad: {e}")


def open_task_manager():
    try:
        subprocess.Popen("taskmgr.exe")
    except Exception as e:
        print(f"[system_control] Could not open Task Manager: {e}")


def open_calculator():
    try:
        subprocess.Popen("calc.exe")
    except Exception as e:
        print(f"[system_control] Could not open Calculator: {e}")


# ---------------------------------------------------------------------------
# Media keys (virtual key codes via keybd_event)
# ---------------------------------------------------------------------------
_VK_MEDIA_PLAY_PAUSE = 0xB3
_VK_MEDIA_NEXT_TRACK = 0xB0
_VK_MEDIA_PREV_TRACK = 0xB1
_KEYEVENTF_EXTENDEDKEY = 0x1
_KEYEVENTF_KEYUP = 0x2


def _press_media_key(vk_code):
    try:
        user32 = ctypes.windll.user32
        user32.keybd_event(vk_code, 0, _KEYEVENTF_EXTENDEDKEY, 0)
        user32.keybd_event(vk_code, 0, _KEYEVENTF_EXTENDEDKEY | _KEYEVENTF_KEYUP, 0)
    except Exception as e:
        print(f"[system_control] Media key failed: {e}")


def play_pause():
    _press_media_key(_VK_MEDIA_PLAY_PAUSE)


def next_track():
    _press_media_key(_VK_MEDIA_NEXT_TRACK)


def previous_track():
    _press_media_key(_VK_MEDIA_PREV_TRACK)


# ---------------------------------------------------------------------------
# Lock PC
# ---------------------------------------------------------------------------
def lock_pc():
    try:
        ctypes.windll.user32.LockWorkStation()
    except Exception as e:
        print(f"[system_control] Lock failed: {e}")