import math
import config

class GestureDetector:
    """
    Rule-based multi-gesture classifier using hand landmark geometry.
    This is the default/fallback classifier used automatically whenever
    no trained ML model (gesture_model.pkl) is present. See
    collect_gesture_data.py + train_gesture_model.py to train a real model
    that replaces these hand-written rules.

    Recognizes: Pinch, Right Pinch, Fist, Open Palm, Point, Peace, Scroll,
    Thumbs Up, Thumbs Down
    """

    FINGER_TIPS = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}
    FINGER_PIPS = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}

    def __init__(self, pinch_threshold_ratio=None):
        self.pinch_threshold_ratio = (
            pinch_threshold_ratio
            if pinch_threshold_ratio is not None
            else config.PINCH_THRESHOLD_RATIO
        )

    def _palm_size(self, pts):
        # Distance wrist -> middle-finger MCP, used as a scale reference so
        # thresholds work regardless of how close the hand is to the camera.
        size = math.hypot(pts[9][0] - pts[0][0], pts[9][1] - pts[0][1])
        return size if size > 1e-6 else 1.0

    def _finger_up(self, pts, tip_id, pip_id):
        return pts[tip_id][1] < pts[pip_id][1]

    def _thumb_extended(self, pts):
        pinky_mcp = pts[17]
        thumb_tip = pts[4]
        thumb_ip = pts[3]
        d_tip = math.hypot(thumb_tip[0] - pinky_mcp[0], thumb_tip[1] - pinky_mcp[1])
        d_ip = math.hypot(thumb_ip[0] - pinky_mcp[0], thumb_ip[1] - pinky_mcp[1])
        return d_tip > d_ip

    def hand_anchor(self, landmarks):
        """Wrist pixel position - used by main.py as a stable reference point
        for tracking scroll movement."""
        pts = {lm[0]: (lm[1], lm[2]) for lm in landmarks}
        return pts[0]

    def classify(self, landmarks):
        """
        landmarks: list of (id, x, y) pixel coordinates for ONE hand.
        Returns (gesture_name: str, confidence_percent: float).
        """

        if not landmarks or len(landmarks) < 21:
            return "None", 0.0

        pts = {lm[0]: (lm[1], lm[2]) for lm in landmarks}
        scale = self._palm_size(pts)

        thumb_tip = pts[4]
        index_tip = pts[8]
        middle_tip = pts[12]

        pinch_index_ratio = math.hypot(index_tip[0] - thumb_tip[0], index_tip[1] - thumb_tip[1]) / scale
        pinch_middle_ratio = math.hypot(middle_tip[0] - thumb_tip[0], middle_tip[1] - thumb_tip[1]) / scale

        fingers_up = {
            name: self._finger_up(pts, self.FINGER_TIPS[name], self.FINGER_PIPS[name])
            for name in self.FINGER_TIPS
        }
        thumb_up = self._thumb_extended(pts)
        num_extended = sum(fingers_up.values()) + (1 if thumb_up else 0)

        # Pinches take priority - small, deliberate gestures that could
        # otherwise be mistaken for a curled fist. Index-thumb wins ties.
        if pinch_index_ratio < self.pinch_threshold_ratio and pinch_index_ratio <= pinch_middle_ratio:
            confidence = max(0.0, min(100.0, (1 - pinch_index_ratio / self.pinch_threshold_ratio) * 100))
            return "Pinch", round(confidence, 1)

        if pinch_middle_ratio < self.pinch_threshold_ratio:
            confidence = max(0.0, min(100.0, (1 - pinch_middle_ratio / self.pinch_threshold_ratio) * 100))
            return "Right Pinch", round(confidence, 1)

        if num_extended == 0:
            return "Fist", 95.0

        if num_extended == 5:
            return "Open Palm", 95.0

        if fingers_up["index"] and not any(
            [fingers_up["middle"], fingers_up["ring"], fingers_up["pinky"], thumb_up]
        ):
            return "Point", 90.0

        # Scroll: index + middle + ring extended, pinky curled
        if fingers_up["index"] and fingers_up["middle"] and fingers_up["ring"] and not fingers_up["pinky"]:
            return "Scroll", 85.0

        # Peace: index + middle extended only
        if fingers_up["index"] and fingers_up["middle"] and not fingers_up["ring"] and not fingers_up["pinky"]:
            return "Peace", 90.0

        if thumb_up and not any(fingers_up.values()):
            wrist_y = pts[0][1]
            if thumb_tip[1] < wrist_y - scale * 0.2:
                return "Thumbs Up", 85.0
            elif thumb_tip[1] > wrist_y + scale * 0.1:
                return "Thumbs Down", 85.0
            return "Thumb", 55.0

        return "None", 40.0
