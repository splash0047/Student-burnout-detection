"""ML model tests for the Student Burnout Detection System."""

import os
import pytest

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "ml",
    "model.pkl",
)


def test_model_file_exists():
    """The trained model.pkl file must exist."""
    assert os.path.exists(MODEL_PATH), f"Model file not found at {MODEL_PATH}"


def test_model_predicts_valid_label():
    """The model should predict a label in {0, 1, 2}."""
    import joblib
    import numpy as np

    model = joblib.load(MODEL_PATH)
    # Sample feature vector: [anxiety, sleep, study, esteem, mental, headache, bp, breathing]
    X = np.array([[10, 3, 3, 15, 0, 2, 1, 1]])
    pred = model.predict(X)
    assert pred[0] in (0, 1, 2)


def test_predict_function_returns_dict_with_label_and_score():
    """The predict() function must return a dict with 'label' and 'score'."""
    from app.predictor import predict

    features = {
        "anxiety_level": 10,
        "sleep_quality": 3,
        "study_load": 3,
        "self_esteem": 15,
        "mental_health_history": 0,
        "headache": 2,
        "blood_pressure": 1,
        "breathing_problem": 1,
    }
    result = predict(features)
    assert isinstance(result, dict)
    assert "label" in result
    assert "score" in result
    assert result["label"] in ("LOW", "MEDIUM", "HIGH")
    assert 0.0 <= result["score"] <= 1.0
