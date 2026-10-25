from datetime import date, datetime
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from src.models import Project, Milestone, Review, ActionItem, ProgressLog
from src.db import load_lexicon_config
from src.services.settings import get_setting

FEATURE_COLS = [
    "progress_gap",
    "action_item_closure_rate",
    "commit_update_trend",
    "days_since_last_update",
    "missed_meetings_total",
    "deadline_slips_count",
    "rubric_score_trend",
    "comment_negative_flag",
    "guide_workload",
    "semester_week"
]

def extract_project_features(db: Session, project: Project, as_of_date: Optional[date] = None) -> Dict[str, float]:
    """
    Extracts all predictive features for a project as of a specified date (or current date):
    1. progress_gap: planned % - actual %
    2. action_item_closure_rate: closed / total action items
    3. commit_update_trend: slope of updates over last N weeks
    4. days_since_last_update: days since latest progress log
    5. missed_meetings_total: sum in lookback window
    6. deadline_slips_count: sum in lookback window
    7. rubric_score_trend: slope or difference in review scores
    8. comment_negative_flag: presence/count of negative keywords in review comments
    9. guide_workload: number of active projects supervised by the project's guide
    10. semester_week: current week into project timeline
    """
    if as_of_date is None:
        as_of_date = date.today()

    lookback_weeks = int(get_setting(db, "feature_params_lookback_weeks", 4))
    lexicon = load_lexicon_config()
    neg_keywords = [k.lower() for k in lexicon.get("negative_keywords", [])]

    # 1. Planned vs Actual Milestone %
    # Planned % as of as_of_date
    milestones = db.query(Milestone).filter(
        Milestone.project_id == project.id,
        Milestone.planned_date <= as_of_date
    ).order_by(Milestone.planned_date.desc()).all()
    
    planned_pct = milestones[0].planned_pct if milestones else 0.0

    # Actual % from latest progress log as of date
    latest_log = db.query(ProgressLog).filter(
        ProgressLog.project_id == project.id,
        ProgressLog.week_start <= as_of_date
    ).order_by(ProgressLog.week_start.desc()).first()

    actual_pct = latest_log.milestone_completion_pct if latest_log else 0.0
    progress_gap = max(-1.0, min(1.0, (planned_pct - actual_pct) / 100.0))

    # 2. Action item closure rate
    action_items = db.query(ActionItem).filter(
        ActionItem.project_id == project.id,
        ActionItem.due_date <= as_of_date
    ).all()
    if action_items:
        completed_count = sum(1 for item in action_items if item.status == "completed")
        closure_rate = completed_count / len(action_items)
    else:
        closure_rate = 1.0  # No action items pending

    # 3. Commit/update trend & missed meetings & deadline slips (over last N logs)
    recent_logs = db.query(ProgressLog).filter(
        ProgressLog.project_id == project.id,
        ProgressLog.week_start <= as_of_date
    ).order_by(ProgressLog.week_start.asc()).all()[-lookback_weeks:]

    if recent_logs:
        updates = [log.commits_or_updates for log in recent_logs]
        if len(updates) > 1:
            x = np.arange(len(updates))
            # Calculate simple linear slope
            slope = float(np.polyfit(x, updates, 1)[0])
        else:
            slope = 0.0
        missed_meetings = sum(log.missed_meetings for log in recent_logs)
        deadline_slips = sum(log.deadline_slips for log in recent_logs)
        days_since_last_update = max(0, (as_of_date - recent_logs[-1].week_start).days)
    else:
        slope = 0.0
        missed_meetings = 0
        deadline_slips = 0
        # If no logs yet, calculate days from project start
        days_since_last_update = max(0, (as_of_date - project.start_date).days)

    # 4. Rubric score trend & comment negative keywords
    reviews = db.query(Review).filter(
        Review.project_id == project.id,
        Review.review_date <= as_of_date
    ).order_by(Review.review_date.asc()).all()

    scores = []
    neg_comment_count = 0
    for rev in reviews:
        # Extract total score if present
        if isinstance(rev.rubric_scores, dict):
            total_score = rev.rubric_scores.get("total", None)
            if total_score is None:
                numeric_vals = [v for v in rev.rubric_scores.values() if isinstance(v, (int, float))]
                total_score = sum(numeric_vals) / len(numeric_vals) if numeric_vals else 0.0
            scores.append(float(total_score))
        
        # Check negative keywords in comment
        comm = (rev.reviewer_comment or "").lower()
        if any(neg_kw in comm for neg_kw in neg_keywords):
            neg_comment_count += 1

    if len(scores) > 1:
        x_scores = np.arange(len(scores))
        rubric_trend = float(np.polyfit(x_scores, scores, 1)[0])
    elif len(scores) == 1:
        rubric_trend = 0.0
    else:
        rubric_trend = 0.0

    # 5. Guide workload
    if project.guide_id:
        active_projects_count = db.query(Project).filter(
            Project.guide_id == project.guide_id,
            Project.status == "active"
        ).count()
    else:
        active_projects_count = 0

    # 6. Semester week
    days_in = max(0, (as_of_date - project.start_date).days)
    semester_week = max(1, days_in // 7 + 1)

    return {
        "progress_gap": float(progress_gap),
        "action_item_closure_rate": float(closure_rate),
        "commit_update_trend": float(slope),
        "days_since_last_update": float(days_since_last_update),
        "missed_meetings_total": float(missed_meetings),
        "deadline_slips_count": float(deadline_slips),
        "rubric_score_trend": float(rubric_trend),
        "comment_negative_flag": float(neg_comment_count),
        "guide_workload": float(active_projects_count),
        "semester_week": float(semester_week)
    }

def get_feature_matrix_for_training(db: Session, delay_threshold_days: int) -> pd.DataFrame:
    """Extracts features and target labels for all completed projects for ML training."""
    completed_projects = db.query(Project).filter(
        Project.status == "completed",
        Project.actual_end_date.isnot(None)
    ).all()

    records = []
    for proj in completed_projects:
        # Check target: 1 if delayed past threshold, 0 otherwise
        delay_days = (proj.actual_end_date - proj.planned_end_date).days
        is_delayed = 1 if delay_days > delay_threshold_days else 0

        # Extract features as of midpoint or planned end date
        eval_date = proj.planned_end_date
        feats = extract_project_features(db, proj, as_of_date=eval_date)
        feats["target"] = is_delayed
        feats["semester"] = proj.semester
        feats["project_id"] = proj.id
        records.append(feats)

    return pd.DataFrame(records)
