"""SQLAlchemy database models for Student Burnout Detection."""

import uuid
from datetime import datetime, timezone
from flask_login import UserMixin
from app import db


class Student(UserMixin, db.Model):
    """Registered student with login capability."""
    __tablename__ = "students"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sessions = db.relationship("Session", backref="student", lazy=True)
    predictions = db.relationship("Prediction", backref="student", lazy=True)

    def set_password(self, password: str, bcrypt):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str, bcrypt) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)

    # Flask-Login requires get_id() to return a string
    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<Student {self.email}>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Session(db.Model):
    """Single study session recorded for a student."""
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    duration_min = db.Column(db.Float, nullable=False, default=0.0)
    typing_speed = db.Column(db.Float, nullable=False, default=0.0)
    break_count = db.Column(db.Integer, nullable=False, default=0)
    anxiety_level = db.Column(db.Integer, nullable=False, default=0)
    sleep_quality = db.Column(db.Integer, nullable=False, default=0)
    study_load = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<Session {self.id} for Student {self.student_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "duration_min": self.duration_min,
            "typing_speed": self.typing_speed,
            "break_count": self.break_count,
            "anxiety_level": self.anxiety_level,
            "sleep_quality": self.sleep_quality,
            "study_load": self.study_load,
        }


class Baseline(db.Model):
    """Per-student normal pattern computed from initial sessions."""
    __tablename__ = "baselines"

    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), primary_key=True)
    avg_typing_speed = db.Column(db.Float, default=0.0)
    avg_duration_min = db.Column(db.Float, default=0.0)
    avg_break_freq = db.Column(db.Float, default=0.0)
    avg_anxiety = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    student = db.relationship("Student", backref=db.backref("baseline", uselist=False))

    def __repr__(self):
        return f"<Baseline for Student {self.student_id}>"

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "avg_typing_speed": self.avg_typing_speed,
            "avg_duration_min": self.avg_duration_min,
            "avg_break_freq": self.avg_break_freq,
            "avg_anxiety": self.avg_anxiety,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Prediction(db.Model):
    """Risk prediction result for a student."""
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(36), db.ForeignKey("students.id"), nullable=False)
    risk_label = db.Column(db.String(10), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    predicted_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Prediction {self.id}: {self.risk_label} for Student {self.student_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "risk_label": self.risk_label,
            "risk_score": self.risk_score,
            "predicted_at": self.predicted_at.isoformat() if self.predicted_at else None,
        }
