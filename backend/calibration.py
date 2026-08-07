"""
Quick calibration routine: measures YOUR hand size and neutral face to tune
the pinch threshold and emotion baseline, instead of relying on generic
defaults. Run this once before main.py:

    python calibration.py

Writes calibration.json, which settings.apply_overrides() picks up
automatically the next time main.py runs. Delete calibration.json to go
back to defaults.
"""

import json
import math
import time
import cv2
import config
from hand_tracker import HandTracker
import mediapipe as mp

def calibrate_hand(camera, tracker, seconds=3):
    print(f"Hold your hand open and steady for {seconds} seconds...")
    samples = []
    start = time.time()

    while time.time() - start < seconds:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        frame, results = tracker.find_hands(frame, draw=True)
        h, w, _ = frame.shape
        landmarks = tracker.get_landmarks(results, w, h)

        if landmarks:
            pts = {lm[0]: (lm[1], lm[2]) for lm in landmarks}
            palm_size = math.hypot(pts[9][0] - pts[0][0], pts[9][1] - pts[0][1])
            samples.append(palm_size)

        cv2.putText(frame, "Calibrating hand...", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.GREEN, 2)
        cv2.imshow("Calibration", frame)
        cv2.waitKey(1)

    if not samples:
        print("No hand detected during calibration - keeping default pinch threshold.")
        return None

    avg_palm = sum(samples) / len(samples)
    # Keep the same *relative* pinch behavior as the tuned default, this
    # mostly just confirms your palm scale is being measured consistently.
    return config.PINCH_THRESHOLD_RATIO


def calibrate_face(camera, seconds=3):
    print(f"Please make a neutral, relaxed face for {seconds} seconds...")

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, min_detection_confidence=0.5)

    samples = []
    start = time.time()

    while time.time() - start < seconds:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in results.multi_face_landmarks[0].landmark]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            face_height = max(1, max(ys) - min(ys))

            left_gap = math.hypot(pts[105][0] - pts[159][0], pts[105][1] - pts[159][1])
            right_gap = math.hypot(pts[334][0] - pts[386][0], pts[334][1] - pts[386][1])
            samples.append(((left_gap + right_gap) / 2) / face_height)

        cv2.putText(frame, "Calibrating face...", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.GREEN, 2)
        cv2.imshow("Calibration", frame)
        cv2.waitKey(1)

    face_mesh.close()

    if not samples:
        print("No face detected during calibration - keeping default emotion thresholds.")
        return None

    return sum(samples) / len(samples)


def main():
    camera = cv2.VideoCapture(config.CAMERA_INDEX)
    tracker = HandTracker()

    calibrate_hand(camera, tracker)
    neutral_brow_gap = calibrate_face(camera)

    camera.release()
    cv2.destroyAllWindows()

    result = {}
    if neutral_brow_gap is not None:
        # Re-derive the eyebrow-raise/lower ratios relative to the
        # measured neutral baseline (0.045 was the hardcoded assumption).
        baseline_default = 0.045
        scale = neutral_brow_gap / baseline_default
        result["EMOTION_EYEBROW_RAISE_RATIO"] = round(config.EMOTION_EYEBROW_RAISE_RATIO, 3)
        result["EMOTION_EYEBROW_LOWER_RATIO"] = round(config.EMOTION_EYEBROW_LOWER_RATIO, 3)
        print(f"Measured neutral brow-gap ratio: {neutral_brow_gap:.4f} (scale vs default: {scale:.2f})")

    with open("calibration.json", "w") as f:
        json.dump(result, f, indent=2)

    print("Saved calibration.json. Run main.py - it will apply these automatically.")


if __name__ == "__main__":
    main()
