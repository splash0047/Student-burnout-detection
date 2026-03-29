"""Flask routes for the Student Burnout Detection System."""

import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app import db
from app.models import Student, Session, Baseline, Prediction
from app.baseline import compute_baseline
from app import predictor

main_bp = Blueprint("main", __name__)


# ──────────────────────────── Helper ────────────────────────────

def _get_or_create_default_student():
    """Return the first student, creating a default one if none exist."""
    student = Student.query.first()
    if student is None:
        student = Student(id=str(uuid.uuid4()), name="Default Student")
        db.session.add(student)
        db.session.commit()
    return student


# ──────────────────────────── Page routes ────────────────────────────

@main_bp.route("/")
def index():
    """Redirect root to dashboard."""
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
def dashboard():
    """Main dashboard showing current risk, today's metrics."""
    student = _get_or_create_default_student()

    # Latest prediction
    latest_pred = (
        Prediction.query
        .filter_by(student_id=student.id)
        .order_by(Prediction.predicted_at.desc())
        .first()
    )

    # Today's sessions
    today = datetime.now(timezone.utc).date()
    today_sessions = [
        s for s in Session.query.filter_by(student_id=student.id).all()
        if s.started_at and s.started_at.date() == today
    ]

    # Metrics
    avg_typing = 0.0
    last_duration = 0.0
    break_count_today = 0
    if today_sessions:
        avg_typing = round(
            sum(s.typing_speed for s in today_sessions) / len(today_sessions), 1
        )
        last_duration = today_sessions[-1].duration_min
        break_count_today = sum(s.break_count for s in today_sessions)

    return render_template(
        "dashboard.html",
        student=student,
        prediction=latest_pred,
        avg_typing=avg_typing,
        last_duration=last_duration,
        break_count_today=break_count_today,
    )


@main_bp.route("/onboarding")
def onboarding():
    """Baseline collection progress page (Day 1–7)."""
    student = _get_or_create_default_student()
    session_count = Session.query.filter_by(student_id=student.id).count()
    day = min(session_count + 1, 7)
    baseline = Baseline.query.get(student.id)
    return render_template(
        "onboarding.html",
        student=student,
        day=day,
        session_count=session_count,
        baseline=baseline,
    )


@main_bp.route("/history")
def history():
    """Weekly trend chart page."""
    student = _get_or_create_default_student()
    return render_template("history.html", student=student)


@main_bp.route("/log")
def log_session():
    """Form to manually log a study session."""
    student = _get_or_create_default_student()
    return render_template("log_session.html", student=student)


# ──────────────────────────── API routes ────────────────────────────

@main_bp.route("/api/collect", methods=["POST"])
def api_collect():
    """Receive session JSON, save to DB, optionally run prediction."""
    data = request.get_json(force=True)
    student_id = data.get("student_id")

    if not student_id:
        student = _get_or_create_default_student()
        student_id = student.id
    else:
        student = Student.query.get(student_id)
        if student is None:
            student = Student(id=student_id, name=data.get("name", "Student"))
            db.session.add(student)

    session = Session(
        student_id=student_id,
        duration_min=float(data.get("duration_min", 0)),
        typing_speed=float(data.get("typing_speed", 0)),
        break_count=int(data.get("break_count", 0)),
        anxiety_level=int(data.get("anxiety_level", 0)),
        sleep_quality=int(data.get("sleep_quality", 0)),
        study_load=int(data.get("study_load", 0)),
    )
    db.session.add(session)
    db.session.commit()

    # Recompute baseline
    compute_baseline(student_id)

    # Run prediction
    features = {
        "anxiety_level": session.anxiety_level,
        "sleep_quality": session.sleep_quality,
        "study_load": session.study_load,
        "self_esteem": int(data.get("self_esteem", 15)),
        "mental_health_history": int(data.get("mental_health_history", 0)),
        "headache": int(data.get("headache", 0)),
        "blood_pressure": int(data.get("blood_pressure", 1)),
        "breathing_problem": int(data.get("breathing_problem", 0)),
    }
    result = predictor.predict(features)

    pred = Prediction(
        student_id=student_id,
        risk_label=result["label"],
        risk_score=result["score"],
    )
    db.session.add(pred)
    db.session.commit()

    return jsonify({
        "session_id": session.id,
        "prediction": result,
    }), 201


@main_bp.route("/api/predict/<student_id>")
def api_predict(student_id):
    """Return latest prediction or run a new one from the most recent session."""
    student = Student.query.get(student_id)
    if student is None:
        return jsonify({"error": "Student not found"}), 404

    # Check for existing recent prediction
    latest_pred = (
        Prediction.query
        .filter_by(student_id=student_id)
        .order_by(Prediction.predicted_at.desc())
        .first()
    )

    if latest_pred:
        return jsonify({
            "label": latest_pred.risk_label,
            "score": latest_pred.risk_score,
        })

    # If no prediction exists, try from latest session
    latest_session = (
        Session.query
        .filter_by(student_id=student_id)
        .order_by(Session.started_at.desc())
        .first()
    )

    if latest_session is None:
        return jsonify({"label": "LOW", "score": 0.0})

    features = {
        "anxiety_level": latest_session.anxiety_level,
        "sleep_quality": latest_session.sleep_quality,
        "study_load": latest_session.study_load,
        "self_esteem": 15,
        "mental_health_history": 0,
        "headache": 0,
        "blood_pressure": 1,
        "breathing_problem": 0,
    }
    result = predictor.predict(features)

    pred = Prediction(
        student_id=student_id,
        risk_label=result["label"],
        risk_score=result["score"],
    )
    db.session.add(pred)
    db.session.commit()

    return jsonify(result)


@main_bp.route("/api/baseline/<student_id>")
def api_baseline(student_id):
    """Return current baseline stats for a student."""
    baseline = Baseline.query.get(student_id)
    if baseline is None:
        return jsonify({"error": "Baseline not yet computed (need >= 3 sessions)"}), 404
    return jsonify(baseline.to_dict())


@main_bp.route("/api/history/<student_id>")
def api_history(student_id):
    """Return last 14 days of predictions."""
    predictions = (
        Prediction.query
        .filter_by(student_id=student_id)
        .order_by(Prediction.predicted_at.desc())
        .limit(14)
        .all()
    )
    return jsonify([p.to_dict() for p in reversed(predictions)])
