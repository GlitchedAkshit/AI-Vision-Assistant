CAMERA_INDEX = 0

FRAME_WIDTH = 640
FRAME_HEIGHT = 480

FRAME_MARGIN = 100

SMOOTHENING = 5

MAX_HANDS = 1

# ==========================
# Colors (BGR, dark theme)
# ==========================
GREEN = (0, 255, 0)
RED = (0, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (60, 60, 60)
BLUE = (255, 180, 0)
YELLOW = (0, 220, 255)
PURPLE = (200, 80, 200)
ORANGE = (0, 140, 255)

# ==========================
# Gesture recognition
# ==========================
PINCH_THRESHOLD_RATIO = 0.35   # fraction of palm size; smaller = tighter pinch required
GESTURE_MODEL_PATH = "gesture_model.pkl"
GESTURE_DATA_PATH = "gesture_data.csv"

EDGE_TRIGGER_GESTURES = {"Pinch", "Right Pinch", "Peace", "Fist", "Open Palm"}
HOLD_REPEAT_GESTURES = {"Thumbs Up", "Thumbs Down"}
ACTION_COOLDOWN = 0.5  # seconds between repeated actions (volume etc.)

# Scroll (three-finger hold gesture)
SCROLL_SPEED = 4            # scroll "clicks" per pixel of vertical movement
SCROLL_DEAD_ZONE = 3        # px of movement to ignore as jitter

# Drag: hold a Pinch this long before it becomes a drag instead of a click
DRAG_HOLD_TIME = 0.35  # seconds

# Auto-pause mouse control if no hand has been seen for this long
IDLE_TIMEOUT = 8.0  # seconds, 0 disables

# ==========================
# System control
# ==========================
VOLUME_STEP = 0.05          # 5% per Thumbs Up/Down trigger
BRIGHTNESS_STEP = 10        # % per +/- key press

# ==========================
# Emotion detection (heuristic thresholds - tune to your lighting/face)
# ==========================
EMOTION_SMILE_THRESHOLD = 0.03
EMOTION_FROWN_THRESHOLD = -0.02
EMOTION_MOUTH_OPEN_THRESHOLD = 0.055
EMOTION_EYEBROW_RAISE_RATIO = 1.15
EMOTION_EYEBROW_LOWER_RATIO = 0.88

# Set False to always use the geometry heuristic even if the `fer` package
# is installed
USE_FER_IF_AVAILABLE = True
FER_INFERENCE_INTERVAL = 8  # run the (slower) FER model every N frames

# ==========================
# Blink / wink detection
# ==========================
EAR_CLOSED_THRESHOLD = 0.20    # fallback absolute floor before baseline is established
EAR_CLOSED_RATIO = 0.72        # eye counted "closed" once EAR drops below baseline * this
EAR_BASELINE_ALPHA = 0.05      # how fast the personal "eyes open" baseline adapts
WINK_CONSECUTIVE_FRAMES = 3    # frames the wink condition must hold before firing (debounce)
WINK_COOLDOWN = 1.0            # seconds between wink-triggered actions

# ==========================
# Emotion smoothing (reduces flicker from single-frame landmark jitter)
# ==========================
EMOTION_EMA_ALPHA = 0.25       # lower = smoother/slower to react, higher = snappier

# ==========================
# Head pose (nod / shake) - experimental, tune per-camera
# ==========================
HEAD_POSE_WINDOW = 30     # frames of history examined for nod/shake
NOD_PITCH_RANGE_DEG = 60  # pitch swing (degrees) within the window to count as a nod
SHAKE_YAW_RANGE_DEG = 40  # yaw swing (degrees) within the window to count as a shake
HEAD_GESTURE_COOLDOWN = 4  # seconds between head-gesture-triggered actions

# ==========================
# Voice feedback / logging
# ==========================
VOICE_FEEDBACK_ENABLED = True
SESSION_LOGGING_ENABLED = True
LOG_DIR = "logs"
