"""Flask routes for the Student Burnout Detection System."""

import uuid
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import Student, Session, Baseline, Prediction
from app.baseline import compute_baseline
from app import predictor

main_bp = Blueprint("main", __name__)


# ──────────────────────────── Auth routes ────────────────────────────

@main_bp.route("/register", methods=["GET", "POST"])
def register():
    """Student registration."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        error = None
        if not name or not email or not password:
            error = "All fields are required."
        elif password != confirm:
            error = "Passwords do not match."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif Student.query.filter_by(email=email).first():
            error = "An account with that email already exists."

        if error:
            flash(error, "error")
            return render_template("register.html")

        student = Student(
            id=str(uuid.uuid4()),
            name=name,
            email=email,
        )
        student.set_password(password, bcrypt)
        db.session.add(student)
        db.session.commit()

        login_user(student)
        flash(f"Welcome, {name}! Start by logging your first session.", "success")
        return redirect(url_for("main.onboarding"))

    return render_template("register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """Student login."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        student = Student.query.filter_by(email=email).first()
        if student and student.check_password(password, bcrypt):
            login_user(student, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@main_bp.route("/logout")
@login_required
def logout():
    """Log out the current student."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


# ──────────────────────────── Page routes ────────────────────────────

@main_bp.route("/")
def index():
    """Redirect root to dashboard."""
    return redirect(url_for("main.dashboard"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Main dashboard showing current risk, today's metrics."""
    student = current_user

    latest_pred = (
        Prediction.query
        .filter_by(student_id=student.id)
        .order_by(Prediction.predicted_at.desc())
        .first()
    )

    today = datetime.now(timezone.utc).date()
    today_sessions = [
        s for s in Session.query.filter_by(student_id=student.id).all()
        if s.started_at and s.started_at.date() == today
    ]

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
@login_required
def onboarding():
    """Baseline collection progress page (Day 1–7)."""
    student = current_user
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
@login_required
def history():
    """Weekly trend chart page."""
    return render_template("history.html", student=current_user)


@main_bp.route("/log")
@login_required
def log_session():
    """Form to manually log a study session."""
    return render_template("log_session.html", student=current_user)


# ──────────────────────────── API routes ────────────────────────────

@main_bp.route("/api/collect", methods=["POST"])
@login_required
def api_collect():
    """Receive session JSON, save to DB, return prediction."""
    data = request.get_json(force=True)
    student = current_user

    session = Session(
        student_id=student.id,
        duration_min=float(data.get("duration_min", 0)),
        typing_speed=float(data.get("typing_speed", 0)),
        break_count=int(data.get("break_count", 0)),
        anxiety_level=int(data.get("anxiety_level", 0)),
        sleep_quality=int(data.get("sleep_quality", 0)),
        study_load=int(data.get("study_load", 0)),
    )
    db.session.add(session)
    db.session.commit()

    compute_baseline(student.id)

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
        student_id=student.id,
        risk_label=result["label"],
        risk_score=result["score"],
    )
    db.session.add(pred)
    db.session.commit()

    return jsonify({"session_id": session.id, "prediction": result}), 201


@main_bp.route("/api/predict/<student_id>")
@login_required
def api_predict(student_id):
    """Return latest prediction or derive from most recent session."""
    if student_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403

    latest_pred = (
        Prediction.query
        .filter_by(student_id=student_id)
        .order_by(Prediction.predicted_at.desc())
        .first()
    )

    if latest_pred:
        return jsonify({"label": latest_pred.risk_label, "score": latest_pred.risk_score})

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
@login_required
def api_baseline(student_id):
    """Return current baseline stats for a student."""
    if student_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403
    baseline = Baseline.query.get(student_id)
    if baseline is None:
        return jsonify({"error": "Baseline not yet computed (need >= 3 sessions)"}), 404
    return jsonify(baseline.to_dict())


@main_bp.route("/api/history/<student_id>")
@login_required
def api_history(student_id):
    """Return last 14 days of predictions."""
    if student_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403
    predictions = (
        Prediction.query
        .filter_by(student_id=student_id)
        .order_by(Prediction.predicted_at.desc())
        .limit(14)
        .all()
    )
    return jsonify([p.to_dict() for p in reversed(predictions)])


@main_bp.route("/api/explain/<student_id>")
@login_required
def api_explain(student_id):
    """Return SHAP explanation for the student's latest prediction."""
    if student_id != current_user.id:
        return jsonify({"error": "Forbidden"}), 403

    latest_session = (
        Session.query
        .filter_by(student_id=student_id)
        .order_by(Session.started_at.desc())
        .first()
    )

    if latest_session is None:
        return jsonify({"error": "No sessions found"}), 404

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

    from app.explainer import explain
    explanation = explain(features)
    return jsonify(explanation)
