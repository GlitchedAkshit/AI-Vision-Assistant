"""
Collects labeled hand-landmark samples for training your own gesture model.

"""

import csv
import cv2
import config
from hand_tracker import HandTracker
from ml_gesture_classifier import MLGestureClassifier

GESTURES = [
    "Fist", "Open Palm", "Peace", "Point",
    "Thumbs Up", "Thumbs Down", "Pinch", "Right Pinch", "Scroll",
]


def save(rows):
    if not rows:
        print("No samples collected - nothing saved.")
        return

    with open(config.GESTURE_DATA_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([f"f{i}" for i in range(len(rows[0]) - 1)] + ["label"])
        writer.writerows(rows)

    print(f"Saved {len(rows)} samples to {config.GESTURE_DATA_PATH}")


def main():
    camera = cv2.VideoCapture(config.CAMERA_INDEX)
    tracker = HandTracker()
    extractor = MLGestureClassifier()  # only used for its extract_features()
    rows = []

    print("Press a number key to label the CURRENT hand pose as a gesture:")
    for i, g in enumerate(GESTURES):
        print(f"  {i} -> {g}")
    print("Press 's' to save and quit, 'q' to quit without saving.\n")

    while True:
        success, frame = camera.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        frame, results = tracker.find_hands(frame)
        h, w, _ = frame.shape
        landmarks = tracker.get_landmarks(results, w, h)

        cv2.putText(
            frame, f"Samples collected: {len(rows)}", (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, config.GREEN, 2
        )
        cv2.imshow("Gesture Data Collection", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        elif key == ord("s"):
            save(rows)
            break
        elif landmarks:
            for i, g in enumerate(GESTURES):
                if key == ord(str(i)):
                    features = extractor.extract_features(landmarks)
                    rows.append(list(features) + [g])
                    print(f"Captured sample for '{g}' (total {len(rows)})")

    camera.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
