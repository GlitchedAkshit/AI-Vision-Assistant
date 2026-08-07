"""
Trains a gesture-recognition model from gesture_data.csv (produced by
collect_gesture_data.py) and saves it to gesture_model.pkl.

main.py automatically uses this trained model instead of the rule-based
GestureDetector whenever gesture_model.pkl is present.
"""

import csv
import numpy as np

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

import config


def main():
    with open(config.GESTURE_DATA_PATH) as f:
        reader = csv.reader(f)
        next(reader)  # header
        rows = list(reader)

    if len(rows) < 20:
        print(f"Only {len(rows)} samples found - collect more with "
              f"collect_gesture_data.py for a reliable model.")

    X = np.array([[float(v) for v in row[:-1]] for row in rows])
    y_raw = [row[-1] for row in rows]

    labels = sorted(set(y_raw))
    label_to_idx = {label: i for i, label in enumerate(labels)}
    y = np.array([label_to_idx[label] for label in y_raw])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    model = RandomForestClassifier(n_estimators=150, random_state=42)
    model.fit(X_train, y_train)

    accuracy = model.score(X_test, y_test)
    print(f"Validation accuracy: {accuracy * 100:.1f}% ({len(X_test)} test samples)")

    joblib.dump({"model": model, "labels": labels}, config.GESTURE_MODEL_PATH)
    print(f"Saved trained model to {config.GESTURE_MODEL_PATH}")


if __name__ == "__main__":
    main()
