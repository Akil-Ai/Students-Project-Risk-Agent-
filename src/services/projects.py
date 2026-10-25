from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import Project, ProjectMember, Milestone, User, Guide, Student, AuditLog
from src.logger import logger

def list_projects_for_user(db: Session, user: User) -> List[Project]:
    """Returns projects scoped by user role: admin sees all, guide sees guided projects, student sees assigned projects."""
    if user.role == "admin":
        return db.query(Project).all()
    elif user.role == "guide":
        if not user.guide_profile:
            return []
        return db.query(Project).filter(Project.guide_id == user.guide_profile.id).all()
    elif user.role == "student":
        if not user.student_profile:
            return []
        memberships = db.query(ProjectMember).filter(ProjectMember.student_id == user.student_profile.id).all()
        proj_ids = [m.project_id for m in memberships]
        return db.query(Project).filter(Project.id.in_(proj_ids)).all() if proj_ids else []
    return []

def get_project_by_id(db: Session, project_id: int, user: Optional[User] = None) -> Optional[Project]:
    """Fetches a project and checks role permissions if user is provided."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not user:
        return project

    # Permission check
    if user.role == "admin":
        return project
    elif user.role == "guide" and user.guide_profile and project.guide_id == user.guide_profile.id:
        return project
    elif user.role == "student" and user.student_profile:
        is_member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project.id,
            ProjectMember.student_id == user.student_profile.id
        ).first()
        if is_member:
            return project
    return None

def create_project(
    db: Session,
    title: str,
    semester: str,
    start_date: date,
    planned_end_date: date,
    type: str = "Major",
    team_size: int = 4,
    guide_id: Optional[int] = None,
    student_ids: Optional[List[int]] = None,
    creator_id: Optional[int] = None
) -> Project:
    """Creates a new project and attaches members."""
    project = Project(
        title=title.strip(),
        semester=semester.strip(),
        start_date=start_date,
        planned_end_date=planned_end_date,
        type=type,
        team_size=team_size,
        guide_id=guide_id,
        status="active"
    )
    db.add(project)
    db.flush()

    if student_ids:
        for sid in student_ids:
            member = ProjectMember(project_id=project.id, student_id=sid)
            db.add(member)

    # Audit log
    audit = AuditLog(
        user_id=creator_id,
        action="CREATE_PROJECT",
        details={"project_id": project.id, "title": project.title, "guide_id": guide_id}
    )
    db.add(audit)
    db.commit()
    db.refresh(project)
    logger.info(f"Created project {project.id}: {project.title}")
    return project

def add_milestone(
    db: Session,
    project_id: int,
    name: str,
    planned_date: date,
    planned_pct: float,
    completed_date: Optional[date] = None
) -> Milestone:
    """Adds a planned milestone to a project."""
    milestone = Milestone(
        project_id=project_id,
        name=name.strip(),
        planned_date=planned_date,
        planned_pct=planned_pct,
        completed_date=completed_date
    )
    db.add(milestone)
    db.commit()
    db.refresh(milestone)
    return milestone
