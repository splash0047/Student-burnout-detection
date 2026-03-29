"""Model evaluation script — generates detailed metrics report.

Loads the trained model and dataset, computes confusion matrix,
per-class precision/recall/F1, and overall accuracy.
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
)
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "stress_dataset.csv")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")

FEATURE_COLS = [
    "anxiety_level",
    "sleep_quality",
    "study_load",
    "self_esteem",
    "mental_health_history",
    "headache",
    "blood_pressure",
    "breathing_problem",
]
TARGET_COL = "stress_level"
TARGET_NAMES = ["LOW", "MEDIUM", "HIGH"]


def main():
    if not os.path.exists(MODEL_PATH):
        print(f"Model not found at {MODEL_PATH}. Run train.py first.")
        return

    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}.")
        return

    model = joblib.load(MODEL_PATH)
    df = pd.read_csv(DATA_PATH)

    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()
    X = X.fillna(X.median())

    # Use same split as training
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("=" * 60)
    print("MODEL EVALUATION REPORT")
    print("=" * 60)
    print(f"\nAccuracy: {acc * 100:.1f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, target_names=TARGET_NAMES))

    print("Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"{'':>12} {'LOW':>8} {'MEDIUM':>8} {'HIGH':>8}")
    for i, name in enumerate(TARGET_NAMES):
        print(f"{name:>12} {cm[i][0]:>8} {cm[i][1]:>8} {cm[i][2]:>8}")
    print()


if __name__ == "__main__":
    main()
