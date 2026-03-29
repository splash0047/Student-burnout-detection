"""Load the trained ML model and expose a predict() function."""

import os
import joblib
import numpy as np

_model = None
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ml",
    "model.pkl",
)

LABEL_MAP = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}

FEATURE_ORDER = [
    "anxiety_level",
    "sleep_quality",
    "study_load",
    "self_esteem",
    "mental_health_history",
    "headache",
    "blood_pressure",
    "breathing_problem",
]


def _load_model():
    """Lazy-load and cache the trained pipeline."""
    global _model
    if _model is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at {_MODEL_PATH}. Run ml/train.py first."
            )
        _model = joblib.load(_MODEL_PATH)
    return _model


def predict(features: dict) -> dict:
    """Run prediction on a feature dictionary.

    Args:
        features: dict with keys matching FEATURE_ORDER.
                  Missing keys default to 0.

    Returns:
        {"label": "LOW"|"MEDIUM"|"HIGH", "score": float}
    """
    model = _load_model()

    # Build feature array in correct order
    row = [float(features.get(col, 0)) for col in FEATURE_ORDER]
    X = np.array([row])

    prediction = int(model.predict(X)[0])
    label = LABEL_MAP.get(prediction, "UNKNOWN")

    # Get probability of predicted class
    probas = model.predict_proba(X)[0]
    score = round(float(probas[prediction]), 4)

    return {"label": label, "score": score}
