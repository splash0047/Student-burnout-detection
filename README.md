# BurnoutGuard — Student Burnout Detection System

Detect early signs of student burnout using behavioural data (typing speed, study duration, break frequency) and machine learning. Provides a **LOW / MEDIUM / HIGH** risk score before burnout peaks.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-orange) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Quick Start

```bash
# 1. Clone and enter project
git clone https://github.com/YOUR_USERNAME/burnout-detection.git
cd burnout-detection

# 2. Create a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate dataset and train the ML model
python data/raw/generate_synthetic.py
python ml/train.py

# 5. Run the Flask app
python run.py
# Open http://127.0.0.1:5000
```

---

## Dataset

The system uses a stress factors dataset with the following features:
| Feature | Range | Description |
|---------|-------|-------------|
| `anxiety_level` | 0–21 | Anxiety scale score |
| `sleep_quality` | 0–5 | 5 = best sleep |
| `study_load` | 0–5 | 5 = heaviest load |
| `self_esteem` | 0–30 | Self-esteem score |
| `mental_health_history` | 0/1 | Past mental health issues |
| `headache` | 0–5 | Headache frequency |
| `blood_pressure` | 0–3 | Blood pressure category |
| `breathing_problem` | 0–5 | Breathing difficulty level |

**Target:** `stress_level` (0=LOW, 1=MEDIUM, 2=HIGH)

To use the Kaggle dataset, download from:  
https://www.kaggle.com/datasets/rxnach/student-stress-factors-a-comprehensive-analysis  
Save to `data/raw/stress_dataset.csv`

---

## Project Structure

```
burnout-detection/
├── app/
│   ├── __init__.py       # Flask factory + SQLAlchemy init
│   ├── routes.py         # All Flask routes
│   ├── models.py         # Student, Session, Baseline, Prediction
│   ├── predictor.py      # Load model.pkl, predict()
│   ├── baseline.py       # Per-student baseline computation
│   ├── templates/        # Jinja2 HTML templates
│   └── static/           # CSS + JS assets
├── ml/
│   ├── train.py          # ML training pipeline
│   ├── evaluate.py       # Metrics report
│   └── model.pkl         # Trained model (auto-generated)
├── data/raw/             # Dataset (gitignored)
├── tests/                # Pytest test suite
├── docs/index.html       # GitHub Pages static dashboard
├── run.py                # App entry point
└── requirements.txt
```

---

## API Reference

### Page Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Redirect to `/dashboard` |
| GET | `/dashboard` | Main dashboard |
| GET | `/history` | Weekly trend chart |
| GET | `/log` | Session log form |
| GET | `/onboarding` | Baseline setup progress |

### API Endpoints

#### POST `/api/collect` — Log a session
```bash
curl -X POST http://127.0.0.1:5000/api/collect \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "YOUR_STUDENT_ID",
    "anxiety_level": 12,
    "sleep_quality": 2,
    "study_load": 4,
    "duration_min": 60,
    "typing_speed": 45,
    "break_count": 1,
    "self_esteem": 15,
    "headache": 3
  }'
```

#### GET `/api/predict/<student_id>` — Get risk prediction
```bash
curl http://127.0.0.1:5000/api/predict/YOUR_STUDENT_ID
# Response: {"label": "HIGH", "score": 0.87}
```

#### GET `/api/baseline/<student_id>` — Get baseline stats
```bash
curl http://127.0.0.1:5000/api/baseline/YOUR_STUDENT_ID
# Response: {"student_id": "...", "avg_typing_speed": 55.3, ...}
```

#### GET `/api/history/<student_id>` — Last 14 days of predictions
```bash
curl http://127.0.0.1:5000/api/history/YOUR_STUDENT_ID
# Response: [{"risk_label": "MEDIUM", "risk_score": 0.63, "predicted_at": "..."}, ...]
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run only API tests
pytest tests/test_api.py -v
```

---

## Deployment

### Render.com

1. Push to GitHub
2. Create a new **Web Service** on Render
3. Configure:
   - **Build command:** `pip install -r requirements.txt && python data/raw/generate_synthetic.py && python ml/train.py`
   - **Start command:** `gunicorn run:app`
   - **Environment variables:**
     - `SECRET_KEY` = (generate a random string)
     - `DATABASE_URL` = `sqlite:///burnout.db`
     - `FLASK_ENV` = `production`

### GitHub Pages

1. Enable GitHub Pages in repo settings → source: `/docs` on `main`
2. Edit `docs/index.html` — enter your Render URL and a student ID

---

## ML Pipeline

The pipeline uses **StandardScaler → RandomForestClassifier** (100 estimators):

```bash
# Train the model
python ml/train.py

# Evaluate with detailed metrics
python ml/evaluate.py
```

---

## Tech Stack

- **Backend:** Flask 3.0.3, Flask-SQLAlchemy 3.1.1, SQLite
- **ML:** scikit-learn 1.5.1 (RandomForestClassifier)
- **Frontend:** Jinja2 templates, Chart.js, vanilla CSS/JS
- **Data:** pandas 2.2.2, NumPy 1.26.4
- **Testing:** pytest 8.2.2
- **Production:** gunicorn 22.0.0

---

## License

MIT
