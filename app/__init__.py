"""Flask application factory with SQLAlchemy, LoginManager, and Bcrypt."""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app(testing=False):
    """Create and configure the Flask application."""
    load_dotenv()

    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

    if testing:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
    else:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///burnout.db")
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialise extensions
    db.init_app(app)
    bcrypt.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Student
        return db.session.get(Student, user_id)

    # Register blueprint
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Create tables
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
