from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from src.models import ProgressLog, Project, AuditLog
from src.logger import logger

def add_progress_log(
    db: Session,
    project_id: int,
    week_start: date,
    milestone_completion_pct: float,
    commits_or_updates: int = 0,
    missed_meetings: int = 0,
    deadline_slips: int = 0,
    notes: str = "",
    creator_id: Optional[int] = None
) -> ProgressLog:
    """Records a weekly progress log submitted by a student or guide."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found.")

    log = ProgressLog(
        project_id=project_id,
        week_start=week_start,
        milestone_completion_pct=min(100.0, max(0.0, float(milestone_completion_pct))),
        commits_or_updates=max(0, int(commits_or_updates)),
        missed_meetings=max(0, int(missed_meetings)),
        deadline_slips=max(0, int(deadline_slips)),
        notes=notes.strip() if notes else ""
    )
    db.add(log)

    # Audit log
    audit = AuditLog(
        user_id=creator_id,
        action="ADD_PROGRESS_LOG",
        details={"project_id": project_id, "milestone_completion_pct": milestone_completion_pct}
    )
    db.add(audit)
    db.commit()
    db.refresh(log)
    logger.info(f"Recorded progress log for project {project_id} (Pct: {milestone_completion_pct}%)")
    return log
