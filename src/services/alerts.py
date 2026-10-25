from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import Project, Alert, RiskScore, AuditLog
from src.services.settings import get_setting
from src.services.notifications import send_alert_notification
from src.logger import logger

def check_and_generate_alerts_for_project(db: Session, project: Project) -> Optional[Alert]:
    """
    Evaluates alert conditions for a project:
    1. Project entered 'High' risk bucket, OR
    2. Risk probability increased by >= jump_threshold compared to the previous score.
    Suppresses duplicates if an open alert of the same type was issued within alert_cooldown_days.
    """
    jump_threshold = float(get_setting(db, "jump_threshold", 0.20))
    cooldown_days = int(get_setting(db, "alert_cooldown_days", 7))
    suggested_actions = get_setting(db, "suggested_actions", {})
    if not isinstance(suggested_actions, dict):
        suggested_actions = {}

    # Get recent scores
    recent_scores = db.query(RiskScore).filter(
        RiskScore.project_id == project.id
    ).order_by(RiskScore.as_of_date.desc()).limit(2).all()

    if not recent_scores:
        return None

    curr_score = recent_scores[0]
    prev_score = recent_scores[1] if len(recent_scores) > 1 else None

    alert_type = None
    if curr_score.bucket == "High":
        alert_type = "HIGH_RISK"
    elif prev_score and (curr_score.probability - prev_score.probability) >= jump_threshold:
        alert_type = "RISK_JUMP"

    if not alert_type:
        return None

    # Check cooldown: has an alert of this type been generated recently?
    cooldown_cutoff = datetime.utcnow() - timedelta(days=cooldown_days)
    recent_alert = db.query(Alert).filter(
        Alert.project_id == project.id,
        Alert.type == alert_type,
        Alert.created_at >= cooldown_cutoff
    ).first()

    if recent_alert:
        logger.info(f"Alert of type {alert_type} for project {project.id} suppressed due to cooldown ({cooldown_days} days).")
        return None

    # Determine suggested action based on top factor
    reasons = [f.get("description", str(f)) for f in curr_score.top_factors] if curr_score.top_factors else ["Elevated risk factors detected."]
    primary_factor = curr_score.top_factors[0].get("factor", "") if curr_score.top_factors else ""

    action = suggested_actions.get(primary_factor)
    if not action:
        if alert_type == "HIGH_RISK":
            action = suggested_actions.get("default_high_risk", "Initiate project intervention and review timeline.")
        else:
            action = "Monitor team progress closely and schedule review meeting."

    alert = Alert(
        project_id=project.id,
        created_at=datetime.utcnow(),
        type=alert_type,
        reasons=reasons,
        suggested_action=action,
        status="open",
        feedback="none"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    logger.info(f"Generated alert {alert.id} ({alert.type}) for project {project.id} ({project.title})")

    # Send notification to Guide
    guide_email = project.guide.user.email if project.guide and project.guide.user else None
    send_alert_notification(
        recipient_email=guide_email,
        project_title=project.title,
        alert_type=alert.type,
        reasons=reasons,
        suggested_action=action
    )

    return alert

def check_and_generate_alerts_all_active(db: Session) -> List[Alert]:
    """Runs alert checks across all active projects."""
    active_projects = db.query(Project).filter(Project.status == "active").all()
    created_alerts = []
    for p in active_projects:
        al = check_and_generate_alerts_for_project(db, p)
        if al:
            created_alerts.append(al)
    return created_alerts

def record_alert_feedback(db: Session, alert_id: int, feedback: str, new_status: Optional[str] = None, user_id: Optional[int] = None) -> Alert:
    """Updates feedback ('useful', 'not_useful') and optionally resolves the alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise ValueError(f"Alert {alert_id} not found.")

    alert.feedback = feedback
    if new_status:
        alert.status = new_status

    audit = AuditLog(
        user_id=user_id,
        action="ALERT_FEEDBACK",
        details={"alert_id": alert_id, "feedback": feedback, "status": alert.status}
    )
    db.add(audit)
    db.commit()
    db.refresh(alert)
    logger.info(f"Recorded feedback '{feedback}' for alert {alert_id}")
    return alert
