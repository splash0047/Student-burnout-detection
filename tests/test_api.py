"""API endpoint tests for the Student Burnout Detection System."""

import json
import pytest
from app import create_app, db
from app.models import Student


@pytest.fixture
def client():
    """Create a test client with an in-memory database."""
    app = create_app(testing=True)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Create a test student
            student = Student(id="test-student-001", name="Test Student")
            db.session.add(student)
            db.session.commit()
        yield client


def test_dashboard_loads(client):
    """GET / should redirect to /dashboard and return 200."""
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200


def test_collect_session(client):
    """POST /api/collect with valid JSON should return 201."""
    payload = {
        "student_id": "test-student-001",
        "anxiety_level": 10,
        "sleep_quality": 3,
        "study_load": 4,
        "duration_min": 45.0,
        "typing_speed": 55.0,
        "break_count": 2,
        "self_esteem": 15,
        "headache": 2,
    }
    response = client.post(
        "/api/collect",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "session_id" in data
    assert "prediction" in data


def test_predict_returns_label(client):
    """GET /api/predict/<id> should return JSON with 'label' key."""
    # First create a session to generate a prediction
    payload = {
        "student_id": "test-student-001",
        "anxiety_level": 12,
        "sleep_quality": 2,
        "study_load": 5,
        "duration_min": 60.0,
        "typing_speed": 40.0,
        "break_count": 1,
    }
    client.post(
        "/api/collect",
        data=json.dumps(payload),
        content_type="application/json",
    )

    response = client.get("/api/predict/test-student-001")
    assert response.status_code == 200
    data = response.get_json()
    assert "label" in data


def test_predict_label_is_valid(client):
    """The risk label must be one of LOW, MEDIUM, HIGH."""
    payload = {
        "student_id": "test-student-001",
        "anxiety_level": 18,
        "sleep_quality": 1,
        "study_load": 5,
        "duration_min": 90.0,
        "typing_speed": 30.0,
        "break_count": 0,
    }
    client.post(
        "/api/collect",
        data=json.dumps(payload),
        content_type="application/json",
    )

    response = client.get("/api/predict/test-student-001")
    data = response.get_json()
    assert data["label"] in ("LOW", "MEDIUM", "HIGH")
