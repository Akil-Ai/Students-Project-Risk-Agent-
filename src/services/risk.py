from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import Project, RiskScore, AuditLog
from src.ml.predict import predict_project_risk
from src.logger import logger

def score_and_record_project_risk(db: Session, project: Project, creator_id: Optional[int] = None) -> RiskScore:
    """Scores project risk, saves history in risk_scores table, and returns the record."""
    pred = predict_project_risk(db, project)

    score_rec = RiskScore(
        project_id=project.id,
        as_of_date=datetime.utcnow(),
        probability=pred["probability"],
        bucket=pred["bucket"],
        top_factors=pred["top_factors"],
        model_version=pred["model_version"]
    )
    db.add(score_rec)
    db.commit()
    db.refresh(score_rec)
    logger.info(f"Recorded risk score for project {project.id} ({project.title}): {pred['bucket']} ({pred['probability']:.1%}) [{pred['model_version']}]")
    return score_rec

def score_all_active_projects(db: Session) -> List[RiskScore]:
    """Scores all currently active projects and records scores."""
    active_projects = db.query(Project).filter(Project.status == "active").all()
    results = []
    for proj in active_projects:
        rec = score_and_record_project_risk(db, proj)
        results.append(rec)
    return results

def get_latest_risk_for_project(db: Session, project_id: int) -> Optional[RiskScore]:
    """Gets the most recent risk score record for a project."""
    return db.query(RiskScore).filter(
        RiskScore.project_id == project_id
    ).order_by(RiskScore.as_of_date.desc()).first()

def get_risk_history_for_project(db: Session, project_id: int) -> List[RiskScore]:
    """Gets chronological risk score history for trend charting."""
    return db.query(RiskScore).filter(
        RiskScore.project_id == project_id
    ).order_by(RiskScore.as_of_date.asc()).all()
