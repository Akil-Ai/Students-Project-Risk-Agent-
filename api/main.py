import io
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import pandas as pd
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from src.db import get_db, init_db, SessionLocal
from src.models import User, Guide, Student, Project, Milestone, Review, ActionItem, ProgressLog, RiskScore, Alert, MLModel, Setting
from src.services.auth import authenticate_user, create_user, bootstrap_admin_if_empty
from src.services.settings import sync_settings_from_config, get_all_settings, update_setting, get_setting
from src.services.projects import list_projects_for_user, get_project_by_id, create_project
from src.services.risk import score_and_record_project_risk, get_latest_risk_for_project, get_risk_history_for_project
from src.services.alerts import record_alert_feedback
from src.services.reviews import add_review, update_action_item_status
from src.services.progress import add_progress_log
from src.ml.train import train_risk_model
from src.importers import (
    import_projects_dataframe,
    import_reviews_dataframe,
    import_progress_dataframe,
    generate_csv_template
)
from src.scheduler import start_scheduler, scheduler

app = FastAPI(
    title="Student Project Risk Agent REST API",
    description="Full REST API powering the React Frontend for Project Risk Tracking, ML Predictions, Alerts, and Administration.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

@app.on_event("startup")
def startup_event():
    init_db()
    db = SessionLocal()
    try:
        sync_settings_from_config(db)
        bootstrap_admin_if_empty(db)
        start_scheduler()
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    user = db.query(User).filter(User.email == token.strip().lower()).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return user

# Schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str
    email: str
    user_id: int

class FeedbackRequest(BaseModel):
    feedback: str
    status: Optional[str] = None

class SettingUpdateRequest(BaseModel):
    key: str
    value: Any

class CreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "student"
    department: Optional[str] = "Computer Science"
    usn_or_roll: Optional[str] = None
    batch_year: Optional[int] = 2026

class ReviewCreateRequest(BaseModel):
    review_date: date
    attendance: float = 1.0
    rubric_presentation: int = 8
    rubric_code: int = 7
    rubric_viva: int = 5
    reviewer_comment: Optional[str] = ""
    action_items_summary: Optional[str] = ""
    action_item_desc: Optional[str] = ""
    action_item_due: Optional[date] = None

class ActionItemUpdateRequest(BaseModel):
    status: str

class ProgressLogCreateRequest(BaseModel):
    week_start: date
    milestone_completion_pct: float
    commits_or_updates: int = 0
    missed_meetings: int = 0
    deadline_slips: int = 0
    notes: Optional[str] = ""

class CreateProjectRequest(BaseModel):
    title: str
    type: str = "Major"
    semester: str = "Fall 2025"
    start_date: date
    planned_end_date: date
    team_size: int = 4
    guide_id: Optional[int] = None

# --- AUTH & USER PROFILE ---

@app.post("/api/v1/auth/token", response_model=TokenResponse)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect institutional email or password"
        )
    return {
        "access_token": user.email,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "user_id": user.id
    }

@app.get("/api/v1/auth/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "department": current_user.guide_profile.department if current_user.guide_profile else None,
        "usn": current_user.student_profile.usn_or_roll if current_user.student_profile else None
    }

# --- STATS / OVERVIEW KPI ---

@app.get("/api/v1/overview")
def get_overview_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projs = list_projects_for_user(db, current_user)
    
    project_rows = []
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0
    unscored_count = 0

    for p in projs:
        risk = get_latest_risk_for_project(db, p.id)
        bucket = risk.bucket if risk else "Unscored"
        prob = risk.probability if risk else 0.0
        factors = risk.top_factors if risk else []
        model_ver = risk.model_version if risk else "None"

        if bucket == "High":
            high_risk_count += 1
        elif bucket == "Medium":
            medium_risk_count += 1
        elif bucket == "Low":
            low_risk_count += 1
        else:
            unscored_count += 1

        top_desc = factors[0].get("description", "-") if factors else "-"

        project_rows.append({
            "id": p.id,
            "title": p.title,
            "type": p.type,
            "semester": p.semester,
            "status": p.status.title(),
            "guide_name": p.guide.user.name if p.guide and p.guide.user else "Unassigned",
            "risk_bucket": bucket,
            "delay_probability": round(prob, 3),
            "top_factor": top_desc,
            "model_version": model_ver,
            "planned_end_date": str(p.planned_end_date)
        })

    return {
        "total_projects": len(projs),
        "high_risk_count": high_risk_count,
        "medium_risk_count": medium_risk_count,
        "low_risk_count": low_risk_count,
        "unscored_count": unscored_count,
        "projects": project_rows
    }

# --- PROJECTS & DETAIL ---

@app.get("/api/v1/projects")
def get_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projs = list_projects_for_user(db, current_user)
    return [{
        "id": p.id,
        "title": p.title,
        "type": p.type,
        "semester": p.semester,
        "status": p.status,
        "guide_name": p.guide.user.name if p.guide and p.guide.user else "Unassigned",
        "planned_end_date": str(p.planned_end_date),
        "start_date": str(p.start_date)
    } for p in projs]

@app.post("/api/v1/projects")
def create_new_project(payload: CreateProjectRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["admin", "guide"]:
        raise HTTPException(status_code=403, detail="Only Guides and Admins can create projects.")
    
    guide_id = payload.guide_id
    if current_user.role == "guide" and current_user.guide_profile:
        guide_id = current_user.guide_profile.id

    p = create_project(
        db=db,
        title=payload.title,
        semester=payload.semester,
        start_date=payload.start_date,
        planned_end_date=payload.planned_end_date,
        type=payload.type,
        team_size=payload.team_size,
        guide_id=guide_id,
        creator_id=current_user.id
    )
    score_and_record_project_risk(db, p, creator_id=current_user.id)
    return {"id": p.id, "title": p.title, "status": p.status}

@app.get("/api/v1/projects/{project_id}")
def get_project_details(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = get_project_by_id(db, project_id, current_user)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    
    risk = get_latest_risk_for_project(db, p.id)
    history = get_risk_history_for_project(db, p.id)
    milestones = db.query(Milestone).filter(Milestone.project_id == p.id).order_by(Milestone.planned_date.asc()).all()
    reviews = db.query(Review).filter(Review.project_id == p.id).order_by(Review.review_date.desc()).all()
    progress_logs = db.query(ProgressLog).filter(ProgressLog.project_id == p.id).order_by(ProgressLog.week_start.desc()).all()
    action_items = db.query(ActionItem).filter(ActionItem.project_id == p.id).order_by(ActionItem.due_date.asc()).all()

    return {
        "id": p.id,
        "title": p.title,
        "type": p.type,
        "team_size": p.team_size,
        "semester": p.semester,
        "status": p.status,
        "start_date": str(p.start_date),
        "planned_end_date": str(p.planned_end_date),
        "guide_name": p.guide.user.name if p.guide and p.guide.user else "Unassigned",
        "latest_risk": {
            "bucket": risk.bucket if risk else "Unscored",
            "probability": risk.probability if risk else None,
            "model_version": risk.model_version if risk else None,
            "top_factors": risk.top_factors if risk else []
        } if risk else None,
        "risk_history": [{
            "id": h.id,
            "date": h.as_of_date.strftime("%Y-%m-%d %H:%M"),
            "probability": h.probability,
            "bucket": h.bucket,
            "model_version": h.model_version
        } for h in history],
        "milestones": [{
            "id": m.id,
            "name": m.name,
            "planned_date": str(m.planned_date),
            "planned_pct": m.planned_pct,
            "completed_date": str(m.completed_date) if m.completed_date else None
        } for m in milestones],
        "reviews": [{
            "id": r.id,
            "review_date": str(r.review_date),
            "attendance": r.attendance,
            "rubric_scores": r.rubric_scores,
            "reviewer_comment": r.reviewer_comment,
            "action_items_summary": r.action_items_summary
        } for r in reviews],
        "action_items": [{
            "id": ai.id,
            "review_id": ai.review_id,
            "description": ai.description,
            "due_date": str(ai.due_date),
            "status": ai.status
        } for ai in action_items],
        "progress_logs": [{
            "id": pl.id,
            "week_start": str(pl.week_start),
            "milestone_completion_pct": pl.milestone_completion_pct,
            "commits_or_updates": pl.commits_or_updates,
            "missed_meetings": pl.missed_meetings,
            "deadline_slips": pl.deadline_slips,
            "notes": pl.notes
        } for pl in progress_logs]
    }

@app.post("/api/v1/projects/{project_id}/score")
def trigger_project_score(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = get_project_by_id(db, project_id, current_user)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    score_rec = score_and_record_project_risk(db, p, creator_id=current_user.id)
    return {
        "project_id": p.id,
        "probability": score_rec.probability,
        "bucket": score_rec.bucket,
        "model_version": score_rec.model_version,
        "top_factors": score_rec.top_factors
    }

# --- PROJECT REVIEWS & ACTION ITEMS ---

@app.post("/api/v1/projects/{project_id}/reviews")
def create_project_review(project_id: int, payload: ReviewCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role not in ["admin", "guide"]:
        raise HTTPException(status_code=403, detail="Only Guides and Admins can conduct reviews.")
    p = get_project_by_id(db, project_id, current_user)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    rubric = {
        "presentation": payload.rubric_presentation,
        "implementation": payload.rubric_code,
        "viva_qa": payload.rubric_viva,
        "total": payload.rubric_presentation + payload.rubric_code + payload.rubric_viva
    }

    action_items_list = []
    if payload.action_item_desc and payload.action_item_desc.strip():
        action_items_list.append({
            "description": payload.action_item_desc.strip(),
            "due_date": payload.action_item_due or payload.review_date,
            "status": "pending"
        })

    rev = add_review(
        db=db,
        project_id=project_id,
        review_date=payload.review_date,
        rubric_scores=rubric,
        attendance=payload.attendance,
        reviewer_comment=payload.reviewer_comment or "",
        action_items_summary=payload.action_items_summary or "",
        action_items_list=action_items_list,
        creator_id=current_user.id
    )
    score_and_record_project_risk(db, p, creator_id=current_user.id)
    return {"id": rev.id, "review_date": str(rev.review_date), "rubric_scores": rev.rubric_scores}

@app.put("/api/v1/action-items/{item_id}")
def update_action_item(item_id: int, payload: ActionItemUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        updated = update_action_item_status(db, item_id, payload.status, user_id=current_user.id)
        return {"id": updated.id, "status": updated.status}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- WEEKLY PROGRESS LOGS ---

@app.post("/api/v1/projects/{project_id}/progress")
def submit_progress_log(project_id: int, payload: ProgressLogCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = get_project_by_id(db, project_id, current_user)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    log = add_progress_log(
        db=db,
        project_id=project_id,
        week_start=payload.week_start,
        milestone_completion_pct=payload.milestone_completion_pct,
        commits_or_updates=payload.commits_or_updates,
        missed_meetings=payload.missed_meetings,
        deadline_slips=payload.deadline_slips,
        notes=payload.notes or "",
        creator_id=current_user.id
    )
    score_and_record_project_risk(db, p, creator_id=current_user.id)
    return {"id": log.id, "milestone_completion_pct": log.milestone_completion_pct}

# --- ALERTS & FEEDBACK ---

@app.get("/api/v1/alerts")
def get_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projs = list_projects_for_user(db, current_user)
    proj_ids = [p.id for p in projs]
    alerts = db.query(Alert).filter(Alert.project_id.in_(proj_ids)).order_by(Alert.created_at.desc()).all()
    
    return [{
        "id": a.id,
        "project_id": a.project_id,
        "project_title": a.project.title if a.project else "Unknown",
        "type": a.type,
        "reasons": a.reasons,
        "suggested_action": a.suggested_action,
        "status": a.status,
        "feedback": a.feedback,
        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M")
    } for a in alerts]

@app.post("/api/v1/alerts/{alert_id}/feedback")
def submit_alert_feedback(alert_id: int, payload: FeedbackRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alert = record_alert_feedback(db, alert_id, feedback=payload.feedback, new_status=payload.status, user_id=current_user.id)
    return {
        "id": alert.id,
        "feedback": alert.feedback,
        "status": alert.status
    }

# --- MODEL MANAGEMENT & RETRAINING ---

@app.get("/api/v1/models")
def get_models_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    
    completed_count = db.query(Project).filter(Project.status == "completed").count()
    min_required = int(get_setting(db, "min_training_projects", 15))
    target_rec = float(get_setting(db, "target_recall", 0.85))
    active_model = db.query(MLModel).filter(MLModel.is_active == True).first()
    all_models = db.query(MLModel).order_by(MLModel.trained_at.desc()).all()

    return {
        "completed_count": completed_count,
        "min_required": min_required,
        "target_recall": target_rec,
        "active_model": {
            "version": active_model.version if active_model else "Rule-Based Heuristic",
            "trained_at": active_model.trained_at.strftime("%Y-%m-%d %H:%M") if active_model else None,
            "metrics": active_model.metrics if active_model else {}
        } if active_model else None,
        "all_models": [{
            "id": m.id,
            "version": m.version,
            "trained_at": m.trained_at.strftime("%Y-%m-%d %H:%M"),
            "metrics": m.metrics,
            "is_active": m.is_active
        } for m in all_models]
    }

@app.post("/api/v1/models/retrain")
def retrain_model_endpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required to trigger retraining")
    try:
        res = train_risk_model(db, force_train=True)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- DATA IMPORTERS & TEMPLATES ---

@app.get("/api/v1/import/template/{entity_type}")
def download_import_template(entity_type: str):
    if entity_type not in ["projects", "reviews", "progress"]:
        raise HTTPException(status_code=400, detail="Invalid entity type. Use 'projects', 'reviews', or 'progress'.")
    csv_text = generate_csv_template(entity_type)
    return Response(content=csv_text, media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename={entity_type}_sample_template.csv"
    })

@app.post("/api/v1/import/{entity_type}")
async def upload_bulk_data(
    entity_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "guide"]:
        raise HTTPException(status_code=403, detail="Only Admins and Guides can perform bulk data imports.")

    contents = await file.read()
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {str(e)}")

    # Default identity mapping for matched column names
    col_mapping = {c: c for c in df.columns}

    if entity_type == "projects":
        success, errors = import_projects_dataframe(db, df, col_mapping, creator_id=current_user.id)
    elif entity_type == "reviews":
        success, errors = import_reviews_dataframe(db, df, col_mapping, creator_id=current_user.id)
    elif entity_type == "progress":
        success, errors = import_progress_dataframe(db, df, col_mapping, creator_id=current_user.id)
    else:
        raise HTTPException(status_code=400, detail="Invalid entity type.")

    return {
        "entity_type": entity_type,
        "success_count": success,
        "error_count": len(errors),
        "errors": errors[:50]
    }

# --- ADMIN USER MANAGEMENT & SETTINGS ---

@app.get("/api/v1/admin/users")
def list_system_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    users = db.query(User).all()
    return [{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "role": u.role,
        "department": u.guide_profile.department if u.guide_profile else None,
        "usn": u.student_profile.usn_or_roll if u.student_profile else None,
        "created_at": u.created_at.strftime("%Y-%m-%d") if u.created_at else None
    } for u in users]

@app.post("/api/v1/admin/users")
def admin_create_user(payload: CreateUserRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    try:
        u = create_user(
            db=db,
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            department=payload.department or "Computer Science",
            usn_or_roll=payload.usn_or_roll,
            batch_year=payload.batch_year or 2026,
            creator_id=current_user.id
        )
        return {"id": u.id, "email": u.email, "role": u.role}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/settings")
def get_settings_endpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return get_all_settings(db)

@app.put("/api/v1/settings")
def update_settings_endpoint(payload: SettingUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    s = update_setting(db, payload.key, payload.value)
    return {"key": s.key, "value": s.value}

@app.get("/api/v1/admin/scheduler")
def get_scheduler_status(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    running = scheduler.running if scheduler else False
    jobs = []
    if running:
        for j in scheduler.get_jobs():
            jobs.append({
                "id": j.id,
                "name": j.name,
                "next_run_time": str(j.next_run_time) if j.next_run_time else "Paused"
            })
    return {"running": running, "jobs": jobs}

# --- PDF / CSV REPORTS EXPORT ---

@app.get("/api/v1/reports/summary")
def get_reports_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projs = list_projects_for_user(db, current_user)
    rows = []
    for p in projs:
        r = get_latest_risk_for_project(db, p.id)
        bucket = r.bucket if r else "Unscored"
        prob = f"{r.probability:.1%}" if r else "N/A"
        factor_desc = r.top_factors[0].get("description", "-") if (r and r.top_factors) else "-"
        rows.append({
            "project_id": p.id,
            "project_title": p.title,
            "type": p.type,
            "semester": p.semester,
            "guide": p.guide.user.name if p.guide and p.guide.user else "Unassigned",
            "risk_bucket": bucket,
            "delay_probability": prob,
            "primary_driver": factor_desc
        })
    return rows

@app.get("/api/v1/reports/pdf")
def export_reports_pdf(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projs = list_projects_for_user(db, current_user)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'RepTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'RepSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=16
    )

    elements.append(Paragraph("Student Project Review & Progress Risk Assessment Report", title_style))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} for {current_user.name} ({current_user.role.title()})", subtitle_style))
    elements.append(Spacer(1, 10))

    headers = ["ID", "Project Title", "Type", "Sem", "Guide", "Risk", "Prob"]
    table_data = [headers]

    for p in projs:
        r = get_latest_risk_for_project(db, p.id)
        bucket = r.bucket if r else "Unscored"
        prob = f"{r.probability:.1%}" if r else "-"
        table_data.append([
            str(p.id),
            p.title[:25] + ("..." if len(p.title) > 25 else ""),
            p.type,
            p.semester,
            (p.guide.user.name[:15] if p.guide and p.guide.user else "None"),
            bucket,
            prob
        ])

    t = Table(table_data, colWidths=[30, 150, 60, 65, 95, 65, 55])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    elements.append(t)
    doc.build(elements)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=project_risk_report.pdf"}
    )
