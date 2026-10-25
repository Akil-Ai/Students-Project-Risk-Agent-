# Student Project Review & Progress Risk Agent

An intelligent, production-ready web application and early-warning intervention agent that predicts which student projects are at risk of completion delay and alerts faculty guides before deadlines slip.

---

## 🏛️ System Architecture

```mermaid
graph TD
    UI[Streamlit Multi-Page Dashboard] --> Svc[Service Layer]
    API[FastAPI REST Layer] --> Svc
    Svc --> Auth[Auth & RBAC (bcrypt)]
    Svc --> Proj[Projects & Milestones Service]
    Svc --> Rev[Reviews & Action Items Service]
    Svc --> Prog[Weekly Progress Logs Service]
    Svc --> Risk[Risk Orchestration & History]
    Svc --> Alert[Alert Engine & Cooldown]
    Svc --> Imp[Bulk Importers with Dynamic Mapping]
    Risk --> ML[ML Engine: LightGBM + SHAP / Cold-Start Rules]
    Sched[APScheduler Heartbeat] --> Risk
    Sched --> Alert
    Alert --> Notif[SMTP / Logging Fallback]
    Svc --> DB[(SQLite / PostgreSQL via SQLAlchemy)]
    Svc --> Cfg[Runtime Settings DB + config.yaml]
```

---

## 🌟 Key Features

1. **Config-Driven Architecture (Zero Hardcoded Values)**:
   - All thresholds (`delay_threshold_days`, `min_training_projects`, `target_recall`, `jump_threshold`, `alert_cooldown_days`), feature weights, bucket cutoffs, and plain-English SHAP templates are defined in `config/config.yaml` and synchronized to the live `settings` database table editable from the Admin UI.
2. **Role-Based Access Control (RBAC)**:
   - **Administrator**: Full system visibility, user provisioning, runtime configuration editing, model retraining, and scheduler monitoring.
   - **Faculty Guide**: Scoped view of supervised projects, conducts reviews, sets action items, triages alerts, and provides feedback (Useful / Not Useful / Resolved).
   - **Student Scholar**: Restricted view of their assigned project team, milestone tracking, and weekly progress submission form.
3. **Machine Learning & Cold-Start Resilience**:
   - **LightGBM Classifier + Baseline Logistic Regression** trained with semester time splits and class-imbalance weighting.
   - Decision threshold automatically tuned to satisfy target recall policy (e.g. 85%).
   - Seamless cold-start fallback to a heuristic multi-factor rule engine when completed project samples are below minimum training thresholds.
   - Model versioning with live version promotion in the UI.
4. **SHAP Explainability**:
   - Computes exact feature attribution scores and formats top-3 positive risk contributors into plain-English sentences via configurable templates.
5. **Smart Alerts & Intervention**:
   - Fires alerts on entering **High Risk** or experiencing a **Risk Jump** week-over-week.
   - Prevents notification fatigue via configurable cooldown periods.
   - Delivers email notifications via SMTP (with graceful fallback to rotating log files if unconfigured).
   - Stores guide feedback to audit labels and fine-tune subsequent retraining iterations.
6. **Bulk Data Migration & Importers**:
   - CSV and Excel bulk import for Projects, Reviews, and Weekly Progress Logs.
   - Dynamic interactive column mapping interface with downloadable templates and downloadable error reports for invalid rows.
7. **REST API**:
   - FastAPI endpoints with Bearer token authentication mirroring the core services for project tracking, scoring, alerts, and model management.
8. **Exportable Reports**:
   - One-click export of institutional risk assessment summaries as CSV or printable PDF (ReportLab).

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10 or 3.11
- Git

### 2. Virtual Environment Setup
```bash
git clone <repository_url>
cd "d:/clg mini project"
python -m venv .venv

# Activate venv on Windows:
.venv\Scripts\activate

# Install dependencies:
pip install -r requirements.txt
```

### 3. Environment Configuration (.env)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default `.env` settings:
```ini
DATABASE_URL=sqlite:///./data/project_agent.db
INITIAL_ADMIN_EMAIL=admin@college.edu
INITIAL_ADMIN_PASSWORD=Admin@123456
INITIAL_ADMIN_NAME="System Administrator"
SECRET_KEY=your-secret-key-change-this-in-production
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=alerts@college.edu
SMTP_USE_TLS=true
```

---

## 🏃 Running the Application

### 1. Generating Demo Data (Optional CLI)
The app runs on a clean empty database by default. To populate realistic multi-semester synthetic data for testing:
```bash
python -m src.seed_demo --projects 30 --semesters 3
```

### 2. Starting the Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```
Open your browser at `http://localhost:8501`.

#### Default Credentials:
- **Admin**: `admin@college.edu` / `Admin@123456`
- **Guide**: `guide1@college.edu` / `Password@123` (after demo seed)
- **Student**: `student1@college.edu` / `Password@123` (after demo seed)

### 3. Starting the FastAPI REST Server
```bash
uvicorn api.main:app --reload --port 8000
```
Explore interactive Swagger API documentation at: `http://localhost:8000/docs`.

---

## 🧪 Running Automated Tests
Run the complete pytest test suite:
```bash
pytest -v
```
Test suite includes:
- `tests/test_auth.py`: Password hashing, user provisioning, RBAC, admin bootstrap.
- `tests/test_rules.py`: Heuristic cold-start scorer, risk buckets, triggered rules.
- `tests/test_importers.py`: CSV parsing, column mapping, row validation, error reports.
- `tests/test_alerts.py`: High-risk triggers, risk jump detection, cooldown suppression, guide feedback.
- `tests/test_pipeline.py`: Full end-to-end integration test (synthetic seeding, training, scoring, alert generation).
