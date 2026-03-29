"""ML Training Pipeline for Student Burnout Detection.

Trains a RandomForestClassifier inside a StandardScaler pipeline
on the stress dataset. Saves the trained model to ml/model.pkl.
"""

import os
import sys
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score

# --- Configuration ---
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

TEST_SIZE = 0.20
RANDOM_STATE = 42
N_ESTIMATORS = 100


def main():
    # 1. Load data
    if not os.path.exists(DATA_PATH):
        print(f"Dataset not found at {DATA_PATH}")
        print("Generating synthetic dataset...")
        gen_script = os.path.join(BASE_DIR, "data", "raw", "generate_synthetic.py")
        os.system(f'"{sys.executable}" "{gen_script}"')

    df = pd.read_csv(DATA_PATH)
    print(f"Loaded dataset: {df.shape[0]} rows, {df.shape[1]} columns")

    # 2. Select features
    X = df[FEATURE_COLS].copy()
    y = df[TARGET_COL].copy()

    # 3. Fill missing values with column median
    X = X.fillna(X.median())

    # 4. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    print(f"Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

    # 5. Build pipeline
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=N_ESTIMATORS,
            random_state=RANDOM_STATE,
        )),
    ])

    # 6. Fit
    pipeline.fit(X_train, y_train)

    # 7. Evaluate
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=TARGET_NAMES))

    # 8. Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    # 9. Summary
    print(f"Model saved to {MODEL_PATH}")
    print(f"Model saved. Accuracy: {acc * 100:.1f}%")

    return acc


if __name__ == "__main__":
    accuracy = main()
    if accuracy < 0.70:
        print("\nWARNING: Accuracy below 70%. Consider regenerating data.")
        sys.exit(1)
