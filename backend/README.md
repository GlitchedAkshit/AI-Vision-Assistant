# AI Vision Assistant

Two-hand gesture mouse/system control, face + emotion detection, blink/wink
and head-pose gestures, voice feedback, and session logging — all running
live from your webcam. Built and tested for **Windows**.

## Quick Setup

```bash
pip install -r requirements.txt
python main.py
```

Every optional package (pycaw, pyttsx3, pystray, fer, etc.) degrades
gracefully — if it's missing, that one feature turns itself off with a
console warning instead of crashing the app.

## Files

| File | Purpose |
|---|---|
| `config.py` | All tunable constants |
| `settings.py` | Loads `settings.json` / `calibration.json` overrides at startup |
| `calibration.py` | One-time routine to measure your hand/face and tune thresholds |
| `hand_tracker.py` | MediaPipe Hands wrapper — tracks up to 2 hands |
| `gesture_detector.py` | Rule-based multi-gesture classifier (default) |
| `ml_gesture_classifier.py` | Loads a **trained** gesture model if present |
| `collect_gesture_data.py` | Records labeled samples for training your own model |
| `train_gesture_model.py` | Trains a RandomForest classifier on your samples |
| `face_analyzer.py` | Face detection, emotion (heuristic or trained `fer` model), blink/wink, head pose |
| `mouse_controller.py` | Cursor move/click/right-click/scroll/drag, pause/resume |
| `system_control.py` | Volume, mute, brightness, screenshot, apps, media keys, lock |
| `voice_feedback.py` | Offline text-to-speech confirmation of actions |
| `session_logger.py` | Logs every fired gesture/action to a timestamped CSV |

## Gesture Map

**Primary (pointer) hand** — the first hand the camera sees:

| Gesture | Action |
|---|---|
| Any pose (not listed below) | Move cursor |
| 🤏 Pinch (thumb+index) | Click — hold past ~0.35s to **drag** instead |
| Pinch (thumb+middle) — "Right Pinch" | Right click |
| ✋ Three fingers up (index+middle+ring) | Scroll — move hand up/down |

**Either hand:**

| Gesture | Action |
|---|---|
| ✌️ Peace | Screenshot |
| 👍 Thumbs Up | Volume up (repeats while held) |
| 👎 Thumbs Down | Volume down (repeats while held) |
| ✊ Fist | Pause mouse control |
| 🖐️ Open Palm | Resume mouse control |

**Face gestures:**

| Gesture | Action |
|---|---|
| 😉 Wink left eye | Toggle mute |
| 😉 Wink right eye | Next track |
| 🙂↕️ Nod head | Play/pause media |
| 🙂↔️ Shake head | Previous track |

Because the hand-gesture vocabulary is limited, a second hand can be used
purely for the "Either hand" actions (e.g. point/click with your right
hand while giving a Thumbs Up with your left to raise volume).

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Q` | Quit |
| `H` | Toggle on-screen help/cheat-sheet |
| `E` | Open File Explorer |
| `O` | Open browser |
| `P` | Play/Pause media |
| `[` / `]` | Previous / Next track |
| `N` | Open Notepad |
| `T` | Open Task Manager |
| `C` | Open Calculator |

The system tray icon (if `pystray`/`pillow` are installed) also has a Quit
option, so you don't need to click back into the camera window to close it.

## Training Your Own Gesture Model

```bash
python collect_gesture_data.py     # hold each gesture, press 0-8 repeatedly, then 's' to save
python train_gesture_model.py      # trains + saves gesture_model.pkl
python main.py                     # automatically detects and uses gesture_model.pkl
```

Collect 30–50+ samples per gesture from a few distances/angles. Delete
`gesture_model.pkl` to go back to the rule-based detector.

## Calibration

```bash
python calibration.py
```

Measures your hand and a neutral face for a few seconds and writes
`calibration.json`, which `main.py` applies automatically. Delete the file
to reset to defaults.

## Settings

```bash
python settings_gui.py
```

Edits the most commonly-tuned values (mouse smoothing, pinch sensitivity,
drag hold time, scroll speed, idle timeout, volume/brightness step, wink
threshold, voice feedback, logging) and saves them to `settings.json`.
Restart `main.py` after saving.

## Real Trained Emotion Model (optional upgrade for the future)

By default, emotion is estimated with a fast, dependency-free geometry
heuristic (mouth/eyebrow landmark distances) — no extra downloads needed,
but approximate. For a genuinely trained CNN instead:

```bash
pip install fer tensorflow
```

`face_analyzer.py` detects `fer` automatically and switches to it
(rate-limited to every `FER_INFERENCE_INTERVAL` frames to protect FPS,
since it's much slower than the heuristic). Set
`USE_FER_IF_AVAILABLE = False` in `config.py` to force the heuristic even
if `fer` is installed.

## Notes & Limitations

- All `system_control.py` code is **Windows-specific** (`pycaw`,
  `ctypes.windll`, `LockWorkStation`, etc.).
- Head-pose nod/shake detection is experimental — it uses `solvePnP` on a
  generic face model and simple angle-swing thresholds
  (`config.NOD_PITCH_RANGE_DEG` / `SHAKE_YAW_RANGE_DEG`); lighting, camera
  angle, and glasses can all affect reliability. Tune the thresholds if it
  fires too often or not enough.
- Emotion/wink/head-pose heuristics all have tunable thresholds in
  `config.py` — expect to nudge them for your face and lighting.
