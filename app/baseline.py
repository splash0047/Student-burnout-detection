"""Compute per-student baseline from their study sessions."""

from datetime import datetime, timezone
from app import db
from app.models import Session, Baseline

MIN_SESSIONS = 3


def compute_baseline(student_id: str):
    """Compute and upsert baseline stats for a student.

    Returns the Baseline object, or None if fewer than MIN_SESSIONS exist.
    """
    sessions = (
        Session.query
        .filter_by(student_id=student_id)
        .order_by(Session.started_at.desc())
        .all()
    )

    if len(sessions) < MIN_SESSIONS:
        return None

    avg_typing = sum(s.typing_speed for s in sessions) / len(sessions)
    avg_duration = sum(s.duration_min for s in sessions) / len(sessions)
    avg_breaks = sum(s.break_count for s in sessions) / len(sessions)
    avg_anxiety = sum(s.anxiety_level for s in sessions) / len(sessions)

    baseline = Baseline.query.get(student_id)
    if baseline is None:
        baseline = Baseline(student_id=student_id)
        db.session.add(baseline)

    baseline.avg_typing_speed = round(avg_typing, 2)
    baseline.avg_duration_min = round(avg_duration, 2)
    baseline.avg_break_freq = round(avg_breaks, 2)
    baseline.avg_anxiety = round(avg_anxiety, 2)
    baseline.updated_at = datetime.now(timezone.utc)

    db.session.commit()
    return baseline
