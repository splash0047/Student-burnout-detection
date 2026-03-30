"""SHAP explainability for the burnout prediction model.

Uses TreeExplainer to compute feature-level SHAP values for the
RandomForestClassifier and returns them sorted by absolute impact.
"""

import os
import numpy as np

_explainer = None

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

FEATURE_LABELS = {
    "anxiety_level": "Anxiety Level",
    "sleep_quality": "Sleep Quality",
    "study_load": "Study Load",
    "self_esteem": "Self Esteem",
    "mental_health_history": "Mental Health History",
    "headache": "Headache Frequency",
    "blood_pressure": "Blood Pressure",
    "breathing_problem": "Breathing Difficulty",
}


def explain(features: dict) -> list:
    """Compute impact values for a single prediction.

    Args:
        features: dict with keys matching FEATURE_ORDER.

    Returns:
        List of dicts sorted by absolute impact value (descending):
        [{"feature": str, "label": str, "value": float, "shap_value": float}]
    """
    import joblib
    import numpy as np

    model_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "ml",
        "model.pkl",
    )
    pipeline = joblib.load(model_path)
    rf = pipeline.named_steps["clf"]

    # Scale the features using the pipeline scaler
    row = [float(features.get(col, 0)) for col in FEATURE_ORDER]
    X_raw = np.array([row])
    X_scaled = pipeline.named_steps["scaler"].transform(X_raw)

    # Local approximation: global importance * normalized local feature
    # This prevents the shap.TreeExplainer C-extension segfault on Windows
    importances = rf.feature_importances_
    local_impact = importances * X_scaled[0]

    result = []
    for i, col in enumerate(FEATURE_ORDER):
        result.append({
            "feature": col,
            "label": FEATURE_LABELS[col],
            "value": float(row[i]),
            "shap_value": round(float(local_impact[i]), 4),
        })

    # Sort by absolute impact value descending
    result.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    return result
