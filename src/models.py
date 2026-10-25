from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, Text, JSON, Table
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="student")  # admin, guide, student
    created_at = Column(DateTime, default=datetime.utcnow)

    guide_profile = relationship("Guide", back_populates="user", uselist=False, cascade="all, delete-orphan")
    student_profile = relationship("Student", back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class Guide(Base):
    __tablename__ = "guides"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    department = Column(String(100), nullable=False, default="Computer Science")
    max_capacity = Column(Integer, nullable=False, default=5)

    user = relationship("User", back_populates="guide_profile")
    projects = relationship("Project", back_populates="guide")

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    usn_or_roll = Column(String(50), unique=True, nullable=False, index=True)
    batch_year = Column(Integer, nullable=False, default=2026)

    user = relationship("User", back_populates="student_profile")
    memberships = relationship("ProjectMember", back_populates="student", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, default="Major")  # Major, Minor, Capstone
    team_size = Column(Integer, nullable=False, default=4)
    guide_id = Column(Integer, ForeignKey("guides.id", ondelete="SET NULL"), nullable=True)
    semester = Column(String(20), nullable=False, index=True)  # e.g., "Fall 2025", "Sem 7"
    start_date = Column(Date, nullable=False)
    planned_end_date = Column(Date, nullable=False)
    actual_end_date = Column(Date, nullable=True)
    status = Column(String(30), nullable=False, default="active")  # active, completed, dropped

    guide = relationship("Guide", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="project", cascade="all, delete-orphan")
    progress_logs = relationship("ProgressLog", back_populates="project", cascade="all, delete-orphan")
    risk_scores = relationship("RiskScore", back_populates="project", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)

    project = relationship("Project", back_populates="members")
    student = relationship("Student", back_populates="memberships")

class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(150), nullable=False)
    planned_date = Column(Date, nullable=False)
    planned_pct = Column(Float, nullable=False)  # cumulative 0.0 - 100.0%
    completed_date = Column(Date, nullable=True)

    project = relationship("Project", back_populates="milestones")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    review_date = Column(Date, nullable=False)
    rubric_scores = Column(JSON, nullable=False, default=dict)  # {"presentation": 8, "impl": 7, "total": 15}
    attendance = Column(Float, nullable=False, default=1.0)  # 0.0 - 1.0 (or attendance count/pct)
    reviewer_comment = Column(Text, nullable=True)
    action_items_summary = Column(Text, nullable=True)

    project = relationship("Project", back_populates="reviews")
    action_items = relationship("ActionItem", back_populates="review", cascade="all, delete-orphan")

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False, default="pending")  # pending, completed, overdue

    review = relationship("Review", back_populates="action_items")
    project = relationship("Project", back_populates="action_items")

class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    week_start = Column(Date, nullable=False)
    milestone_completion_pct = Column(Float, nullable=False, default=0.0)  # 0.0 - 100.0%
    commits_or_updates = Column(Integer, nullable=False, default=0)
    missed_meetings = Column(Integer, nullable=False, default=0)
    deadline_slips = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="progress_logs")

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    as_of_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    probability = Column(Float, nullable=False)  # 0.0 - 1.0
    bucket = Column(String(20), nullable=False)  # Low, Medium, High
    top_factors = Column(JSON, nullable=False, default=list)  # [{"factor": "progress_gap", "impact": 0.35, "description": "..."}]
    model_version = Column(String(50), nullable=False, default="rule-based")

    project = relationship("Project", back_populates="risk_scores")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    type = Column(String(50), nullable=False)  # HIGH_RISK, RISK_JUMP
    reasons = Column(JSON, nullable=False, default=list)  # list of trigger explanations
    suggested_action = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="open")  # open, resolved, dismissed
    feedback = Column(String(30), nullable=False, default="none")  # useful, not_useful, none

    project = relationship("Project", back_populates="alerts")

class MLModel(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), unique=True, nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metrics = Column(JSON, nullable=False, default=dict)  # {"roc_auc": 0.88, "precision": 0.85, ...}
    path = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="audit_logs")
