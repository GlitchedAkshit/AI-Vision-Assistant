import math
import time
from collections import deque
import cv2
import numpy as np
import mediapipe as mp
import config

try:
    from fer import FER
    _FER_IMPORT_OK = True
except ImportError:
    _FER_IMPORT_OK = False


# 3D reference face model (arbitrary units) for head-pose estimation via
# solvePnP, paired with matching 2D FaceMesh landmark indices below.
_MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),          # Nose tip
    (0.0, -330.0, -65.0),     # Chin
    (-225.0, 170.0, -135.0),  # Left eye, left corner
    (225.0, 170.0, -135.0),   # Right eye, right corner
    (-150.0, -150.0, -125.0), # Mouth, left corner
    (150.0, -150.0, -125.0),  # Mouth, right corner
], dtype=np.float64)

_POSE_LANDMARK_IDS = [1, 152, 33, 263, 61, 291]  # nose, chin, L-eye, R-eye, L-mouth, R-mouth

# Eye contour indices (6 points each) for eye-aspect-ratio (EAR) blink/wink detection
_LEFT_EYE_IDS = [33, 160, 158, 133, 153, 144]
_RIGHT_EYE_IDS = [362, 385, 387, 263, 373, 380]


class FaceAnalyzer:
    """
    Face detection (bounding box + landmarks + count), a geometry-based
    emotion estimate (optionally upgraded by the real trained `fer` model
    if installed), blink/wink detection, and experimental head-pose
    nod/shake detection.
    """

    def __init__(self, max_faces=2, detection_confidence=0.7, tracking_confidence=0.7,
                 use_fer=None):
        self.mp_face_mesh = mp.solutions.face_mesh

        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=max_faces,
            refine_landmarks=False,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )

        want_fer = config.USE_FER_IF_AVAILABLE if use_fer is None else use_fer
        self.use_fer = want_fer and _FER_IMPORT_OK
        self._fer = None
        self._fer_frame_counter = 0
        self._last_fer_result = None  # (emotion, confidence) cache between skipped frames

        if self.use_fer:
            try:
                self._fer = FER(mtcnn=False)
                print("[face_analyzer] Using trained FER model for emotion detection.")
            except Exception as e:
                print(f"[face_analyzer] Could not initialize FER ({e}) - "
                      f"falling back to geometry heuristic.")
                self.use_fer = False
        elif want_fer and not _FER_IMPORT_OK:
            print("[face_analyzer] `fer` package not installed - using geometry "
                  "heuristic for emotion. Run: pip install fer tensorflow")

        # Head-pose history (primary face only)
        self._pitch_history = deque(maxlen=config.HEAD_POSE_WINDOW)
        self._yaw_history = deque(maxlen=config.HEAD_POSE_WINDOW)
        self._last_nod_time = 0.0
        self._last_shake_time = 0.0

        # Wink cooldown/debounce state (primary face only)
        self._last_wink_time = 0.0
        self._ear_baseline = None          # adaptive "eyes open" EAR, learned per-user
        self._wink_candidate = None
        self._wink_streak = 0

        # Emotion smoothing state (primary face's heuristic ratios)
        self._lift_ema = None
        self._mouth_open_ema = None
        self._brow_gap_ema = None

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def analyze(self, frame, draw=True):
        """
        Returns (frame, faces). faces is a list of dicts:
            bbox, emotion, emotion_confidence, ear_left, ear_right,
            wink_event ("Left"/"Right"/None), nod_event (bool), shake_event (bool)
        Wink/nod/shake are only computed for the first (primary) face.
        """
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        faces = []

        if not results.multi_face_landmarks:
            return frame, faces

        for i, face_landmarks in enumerate(results.multi_face_landmarks):
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]

            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            bbox = (min(xs), min(ys), max(xs), max(ys))

            emotion, emotion_conf = self._classify_emotion(pts, bbox, frame, is_primary=(i == 0))

            ear_left = self._eye_aspect_ratio(pts, _LEFT_EYE_IDS)
            ear_right = self._eye_aspect_ratio(pts, _RIGHT_EYE_IDS)

            wink_event = None
            nod_event = False
            shake_event = False

            if i == 0:
                wink_event = self._detect_wink(ear_left, ear_right)
                nod_event, shake_event = self._detect_head_gesture(pts, w, h)

            faces.append({
                "bbox": bbox,
                "emotion": emotion,
                "confidence": emotion_conf,
                "ear_left": ear_left,
                "ear_right": ear_right,
                "wink_event": wink_event,
                "nod_event": nod_event,
                "shake_event": shake_event,
            })

            if draw:
                cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), config.BLUE, 1)
                for p in pts[::4]:
                    cv2.circle(frame, p, 1, config.BLUE, -1)

        self._fer_frame_counter += 1
        return frame, faces

    # ------------------------------------------------------------------
    # Emotion (geometry heuristic, optionally overridden by trained FER model)
    # ------------------------------------------------------------------
    def _dist(self, a, b):
        return math.hypot(a[0] - b[0], a[1] - b[1])

    def _classify_emotion(self, pts, bbox, frame, is_primary):
        # Always compute the fast heuristic as a baseline/fallback.
        heuristic = self._classify_emotion_heuristic(pts, bbox, is_primary=is_primary)

        if not (self.use_fer and is_primary):
            return heuristic

        # Rate-limit the (much slower) trained model.
        if self._fer_frame_counter % config.FER_INFERENCE_INTERVAL != 0:
            return self._last_fer_result or heuristic

        x1, y1, x2, y2 = bbox
        pad_x = int((x2 - x1) * 0.25)
        pad_y = int((y2 - y1) * 0.25)
        h, w, _ = frame.shape
        crop = frame[max(0, y1 - pad_y):min(h, y2 + pad_y), max(0, x1 - pad_x):min(w, x2 + pad_x)]

        if crop.size == 0:
            return heuristic

        try:
            results = self._fer.detect_emotions(crop)
            if results:
                emotions = results[0]["emotions"]
                best = max(emotions, key=emotions.get)
                result = (best.capitalize(), round(emotions[best] * 100, 1))
                self._last_fer_result = result
                return result
        except Exception as e:
            print(f"[face_analyzer] FER inference error: {e}")

        return heuristic

    def _classify_emotion_heuristic(self, pts, bbox, is_primary=False):
        mouth_open_ratio, lift_ratio, brow_gap_ratio = self._compute_emotion_ratios(pts, bbox)

        if is_primary:
            alpha = config.EMOTION_EMA_ALPHA
            self._mouth_open_ema = mouth_open_ratio if self._mouth_open_ema is None else (
                alpha * mouth_open_ratio + (1 - alpha) * self._mouth_open_ema
            )
            self._lift_ema = lift_ratio if self._lift_ema is None else (
                alpha * lift_ratio + (1 - alpha) * self._lift_ema
            )
            self._brow_gap_ema = brow_gap_ratio if self._brow_gap_ema is None else (
                alpha * brow_gap_ratio + (1 - alpha) * self._brow_gap_ema
            )
            mouth_open_ratio, lift_ratio, brow_gap_ratio = (
                self._mouth_open_ema, self._lift_ema, self._brow_gap_ema
            )

        return self._classify_from_ratios(mouth_open_ratio, lift_ratio, brow_gap_ratio)

    def _compute_emotion_ratios(self, pts, bbox):
        face_width = max(1, bbox[2] - bbox[0])
        face_height = max(1, bbox[3] - bbox[1])

        mouth_left = pts[61]
        mouth_right = pts[291]
        mouth_top = pts[13]
        mouth_bottom = pts[14]

        mouth_open_ratio = self._dist(mouth_top, mouth_bottom) / face_height
        mouth_center_y = (mouth_top[1] + mouth_bottom[1]) / 2
        corner_avg_y = (mouth_left[1] + mouth_right[1]) / 2
        lift_ratio = (mouth_center_y - corner_avg_y) / face_height

        left_brow_gap = self._dist(pts[105], pts[159])
        right_brow_gap = self._dist(pts[334], pts[386])
        brow_gap_ratio = ((left_brow_gap + right_brow_gap) / 2) / face_height

        return mouth_open_ratio, lift_ratio, brow_gap_ratio

    def _classify_from_ratios(self, mouth_open_ratio, lift_ratio, brow_gap_ratio):
        baseline_brow = 0.045

        if (mouth_open_ratio > config.EMOTION_MOUTH_OPEN_THRESHOLD
                and brow_gap_ratio > baseline_brow * config.EMOTION_EYEBROW_RAISE_RATIO):
            return "Surprise", min(100.0, mouth_open_ratio * 900)

        if lift_ratio > config.EMOTION_SMILE_THRESHOLD:
            return "Happy", min(100.0, lift_ratio * 1800)

        if lift_ratio < config.EMOTION_FROWN_THRESHOLD:
            return "Sad", min(100.0, abs(lift_ratio) * 1800)

        if brow_gap_ratio < baseline_brow * config.EMOTION_EYEBROW_LOWER_RATIO:
            return "Angry", min(100.0, (baseline_brow - brow_gap_ratio) * 1800)

        return "Neutral", 60.0

    # ------------------------------------------------------------------
    # Blink / wink (eye-aspect-ratio)
    # ------------------------------------------------------------------
    def _eye_aspect_ratio(self, pts, ids):
        p1, p2, p3, p4, p5, p6 = [pts[i] for i in ids]
        vertical = self._dist(p2, p6) + self._dist(p3, p5)
        horizontal = self._dist(p1, p4)
        if horizontal < 1e-6:
            return 0.3
        return vertical / (2.0 * horizontal)

    def _is_closed(self, ear):
        # Prefer the personal adaptive baseline once we have one (accounts
        # for your specific eye shape/camera angle); fall back to the fixed
        # threshold until enough "eyes open" frames have been seen.
        if self._ear_baseline is not None:
            return ear < self._ear_baseline * config.EAR_CLOSED_RATIO
        return ear < config.EAR_CLOSED_THRESHOLD

    def _detect_wink(self, ear_left, ear_right):
        now = time.time()

        left_closed = self._is_closed(ear_left)
        right_closed = self._is_closed(ear_right)

        # Only adapt the "eyes open" baseline while NOT winking, so the
        # wink itself doesn't drag the baseline down.
        if not left_closed and not right_closed:
            avg_ear = (ear_left + ear_right) / 2.0
            alpha = config.EAR_BASELINE_ALPHA
            self._ear_baseline = avg_ear if self._ear_baseline is None else (
                alpha * avg_ear + (1 - alpha) * self._ear_baseline
            )

        candidate = None
        if left_closed and not right_closed:
            candidate = "Left"
        elif right_closed and not left_closed:
            candidate = "Right"

        # Debounce: require several consecutive frames of the same
        # candidate before it counts, so a single jittery/blinking frame
        # doesn't fire a false wink.
        if candidate is not None and candidate == self._wink_candidate:
            self._wink_streak += 1
        else:
            self._wink_candidate = candidate
            self._wink_streak = 1 if candidate else 0

        event = None
        if (
            candidate is not None
            and self._wink_streak >= config.WINK_CONSECUTIVE_FRAMES
            and now - self._last_wink_time >= config.WINK_COOLDOWN
        ):
            event = candidate
            self._last_wink_time = now
            self._wink_streak = 0
            self._wink_candidate = None

        return event

    # ------------------------------------------------------------------
    # Head pose (nod / shake)
    # ------------------------------------------------------------------
    def _detect_head_gesture(self, pts, frame_w, frame_h):
        image_points = np.array([pts[i] for i in _POSE_LANDMARK_IDS], dtype=np.float64)

        focal_length = frame_w
        center = (frame_w / 2, frame_h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1],
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4, 1))

        success, rotation_vector, _ = cv2.solvePnP(
            _MODEL_POINTS_3D, image_points, camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return False, False

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)
        sy = math.sqrt(rotation_matrix[0, 0] ** 2 + rotation_matrix[1, 0] ** 2)
        pitch = math.degrees(math.atan2(-rotation_matrix[2, 0], sy))
        yaw = math.degrees(math.atan2(rotation_matrix[1, 0], rotation_matrix[0, 0]))

        self._pitch_history.append(pitch)
        self._yaw_history.append(yaw)

        nod_event = False
        shake_event = False
        now = time.time()

        if len(self._pitch_history) == self._pitch_history.maxlen:
            pitch_range = max(self._pitch_history) - min(self._pitch_history)
            if pitch_range > config.NOD_PITCH_RANGE_DEG and now - self._last_nod_time > config.HEAD_GESTURE_COOLDOWN:
                nod_event = True
                self._last_nod_time = now
                self._pitch_history.clear()

        if len(self._yaw_history) == self._yaw_history.maxlen:
            yaw_range = max(self._yaw_history) - min(self._yaw_history)
            if yaw_range > config.SHAKE_YAW_RANGE_DEG and now - self._last_shake_time > config.HEAD_GESTURE_COOLDOWN:
                shake_event = True
                self._last_shake_time = now
                self._yaw_history.clear()

        return nod_event, shake_event
