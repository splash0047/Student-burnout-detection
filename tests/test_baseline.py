"""Baseline computation tests."""

import pytest
from app import create_app, db
from app.models import Student, Session
from app.baseline import compute_baseline


@pytest.fixture
def app_ctx():
    """Create an app context with an in-memory database."""
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        student = Student(id="baseline-test-001", name="Baseline Tester")
        db.session.add(student)
        db.session.commit()
        yield app


def _add_session(student_id, typing_speed=50.0, duration=45.0, breaks=2, anxiety=5):
    """Helper to add a session."""
    s = Session(
        student_id=student_id,
        typing_speed=typing_speed,
        duration_min=duration,
        break_count=breaks,
        anxiety_level=anxiety,
        sleep_quality=3,
        study_load=3,
    )
    db.session.add(s)
    db.session.commit()


def test_baseline_requires_minimum_sessions(app_ctx):
    """Baseline should return None if fewer than 3 sessions exist."""
    with app_ctx.app_context():
        _add_session("baseline-test-001", typing_speed=50)
        _add_session("baseline-test-001", typing_speed=60)
        result = compute_baseline("baseline-test-001")
        assert result is None


def test_baseline_computed_from_sessions(app_ctx):
    """Baseline should compute averages from >= 3 sessions."""
    with app_ctx.app_context():
        _add_session("baseline-test-001", typing_speed=50, duration=30, breaks=1, anxiety=4)
        _add_session("baseline-test-001", typing_speed=60, duration=40, breaks=2, anxiety=6)
        _add_session("baseline-test-001", typing_speed=70, duration=50, breaks=3, anxiety=8)

        baseline = compute_baseline("baseline-test-001")
        assert baseline is not None
        assert baseline.avg_typing_speed == 60.0
        assert baseline.avg_duration_min == 40.0
        assert baseline.avg_break_freq == 2.0
        assert baseline.avg_anxiety == 6.0
