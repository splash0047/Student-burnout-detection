"""Entry point for the Student Burnout Detection System."""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
