import os
import numpy as np

try:
    import joblib
except ImportError:
    joblib = None

import config


class MLGestureClassifier:
    """
    Loads a trained gesture-recognition model (produced by
    train_gesture_model.py) and predicts gestures from hand landmarks.

    If no trained model exists yet, is_ready() returns False and main.py
    will fall back to the rule-based GestureDetector automatically.
    """

    def __init__(self, model_path=None):
        self.model = None
        self.labels = None

        path = model_path or config.GESTURE_MODEL_PATH

        if joblib is not None and os.path.exists(path):
            data = joblib.load(path)
            self.model = data["model"]
            self.labels = data["labels"]

    def is_ready(self):
        return self.model is not None

    def extract_features(self, landmarks):
        """
        Converts raw (id, x, y) pixel landmarks into a scale/position
        invariant feature vector: every point is shifted so the wrist is
        the origin, then scaled by wrist->middle-MCP distance.
        """
        pts = np.array([[lm[1], lm[2]] for lm in landmarks], dtype=np.float32)
        wrist = pts[0].copy()
        pts -= wrist

        scale = np.linalg.norm(pts[9])
        if scale < 1e-6:
            scale = 1.0
        pts /= scale

        return pts.flatten()

    def predict(self, landmarks):
        """
        Returns (gesture_name, confidence_percent), or (None, 0.0) if the
        model isn't loaded.
        """
        if self.model is None or not landmarks or len(landmarks) < 21:
            return None, 0.0

        features = self.extract_features(landmarks).reshape(1, -1)
        probs = self.model.predict_proba(features)[0]
        idx = int(np.argmax(probs))

        return self.labels[idx], round(float(probs[idx]) * 100, 1)
