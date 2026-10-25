import io
from datetime import datetime, date
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
from sqlalchemy.orm import Session
from src.models import Project, Guide, Student, Review, ProgressLog, Milestone, ProjectMember
from src.services.projects import create_project
from src.services.reviews import add_review
from src.services.progress import add_progress_log
from src.logger import logger

def parse_date_safe(val: Any) -> Optional[date]:
    """Parses various date formats safely."""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val
    val_str = str(val).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(val_str, fmt).date()
        except ValueError:
            pass
    return None

def import_projects_dataframe(
    db: Session,
    df: pd.DataFrame,
    column_mapping: Dict[str, str],
    creator_id: Optional[int] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """
    Imports projects from DataFrame with dynamic column mapping and row validation.
    Returns: (successful_count, error_rows)
    """
    success_count = 0
    errors = []

    # Invert mapping: standard_key -> file_column
    inv_map = {v: k for k, v in column_mapping.items()}

    for idx, row in df.iterrows():
        row_num = idx + 2  # 1-indexed header + 1
        try:
            title_col = inv_map.get("title")
            title = str(row[title_col]).strip() if title_col and not pd.isna(row[title_col]) else None
            if not title:
                errors.append({"row": row_num, "error": "Missing project title", "data": row.to_dict()})
                continue

            sem_col = inv_map.get("semester")
            semester = str(row[sem_col]).strip() if sem_col and not pd.isna(row[sem_col]) else "Fall 2025"

            start_col = inv_map.get("start_date")
            start_d = parse_date_safe(row[start_col]) if start_col else None
            if not start_d:
                start_d = date.today()

            end_col = inv_map.get("planned_end_date")
            end_d = parse_date_safe(row[end_col]) if end_col else None
            if not end_d:
                errors.append({"row": row_num, "error": "Invalid or missing planned_end_date", "data": row.to_dict()})
                continue

            type_col = inv_map.get("type")
            p_type = str(row[type_col]).strip() if type_col and not pd.isna(row[type_col]) else "Major"

            team_col = inv_map.get("team_size")
            try:
                team_size = int(row[team_col]) if team_col and not pd.isna(row[team_col]) else 4
            except ValueError:
                team_size = 4

            # Optional guide by email or guide id
            guide_col = inv_map.get("guide_email")
            guide_id = None
            if guide_col and not pd.isna(row[guide_col]):
                email = str(row[guide_col]).strip().lower()
                guide_match = db.query(Guide).join(Guide.user).filter(Guide.user.has(email=email)).first()
                if guide_match:
                    guide_id = guide_match.id

            proj = create_project(
                db=db,
                title=title,
                semester=semester,
                start_date=start_d,
                planned_end_date=end_d,
                type=p_type,
                team_size=team_size,
                guide_id=guide_id,
                creator_id=creator_id
            )
            success_count += 1
        except Exception as e:
            errors.append({"row": row_num, "error": str(e), "data": row.to_dict()})

    return success_count, errors

def import_reviews_dataframe(
    db: Session,
    df: pd.DataFrame,
    column_mapping: Dict[str, str],
    creator_id: Optional[int] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """Imports reviews with validation."""
    success_count = 0
    errors = []
    inv_map = {v: k for k, v in column_mapping.items()}

    for idx, row in df.iterrows():
        row_num = idx + 2
        try:
            pid_col = inv_map.get("project_id")
            if not pid_col or pd.isna(row[pid_col]):
                errors.append({"row": row_num, "error": "Missing project_id", "data": row.to_dict()})
                continue
            project_id = int(row[pid_col])

            proj = db.query(Project).filter(Project.id == project_id).first()
            if not proj:
                errors.append({"row": row_num, "error": f"Project ID {project_id} does not exist", "data": row.to_dict()})
                continue

            rdate_col = inv_map.get("review_date")
            rev_date = parse_date_safe(row[rdate_col]) if rdate_col else date.today()
            if not rev_date:
                rev_date = date.today()

            score_col = inv_map.get("score")
            score_val = float(row[score_col]) if score_col and not pd.isna(row[score_col]) else 15.0

            comment_col = inv_map.get("comment")
            comment = str(row[comment_col]).strip() if comment_col and not pd.isna(row[comment_col]) else ""

            add_review(
                db=db,
                project_id=project_id,
                review_date=rev_date,
                rubric_scores={"total": score_val},
                attendance=1.0,
                reviewer_comment=comment,
                creator_id=creator_id
            )
            success_count += 1
        except Exception as e:
            errors.append({"row": row_num, "error": str(e), "data": row.to_dict()})

    return success_count, errors

def import_progress_dataframe(
    db: Session,
    df: pd.DataFrame,
    column_mapping: Dict[str, str],
    creator_id: Optional[int] = None
) -> Tuple[int, List[Dict[str, Any]]]:
    """Imports weekly progress logs with validation."""
    success_count = 0
    errors = []
    inv_map = {v: k for k, v in column_mapping.items()}

    for idx, row in df.iterrows():
        row_num = idx + 2
        try:
            pid_col = inv_map.get("project_id")
            if not pid_col or pd.isna(row[pid_col]):
                errors.append({"row": row_num, "error": "Missing project_id", "data": row.to_dict()})
                continue
            project_id = int(row[pid_col])

            proj = db.query(Project).filter(Project.id == project_id).first()
            if not proj:
                errors.append({"row": row_num, "error": f"Project ID {project_id} does not exist", "data": row.to_dict()})
                continue

            wstart_col = inv_map.get("week_start")
            week_start = parse_date_safe(row[wstart_col]) if wstart_col else date.today()
            if not week_start:
                week_start = date.today()

            pct_col = inv_map.get("completion_pct")
            pct = float(row[pct_col]) if pct_col and not pd.isna(row[pct_col]) else 0.0

            updates_col = inv_map.get("commits_or_updates")
            updates = int(row[updates_col]) if updates_col and not pd.isna(row[updates_col]) else 0

            slips_col = inv_map.get("deadline_slips")
            slips = int(row[slips_col]) if slips_col and not pd.isna(row[slips_col]) else 0

            missed_col = inv_map.get("missed_meetings")
            missed = int(row[missed_col]) if missed_col and not pd.isna(row[missed_col]) else 0

            add_progress_log(
                db=db,
                project_id=project_id,
                week_start=week_start,
                milestone_completion_pct=pct,
                commits_or_updates=updates,
                missed_meetings=missed,
                deadline_slips=slips,
                creator_id=creator_id
            )
            success_count += 1
        except Exception as e:
            errors.append({"row": row_num, "error": str(e), "data": row.to_dict()})

    return success_count, errors

def generate_csv_template(template_type: str) -> str:
    """Generates a downloadable CSV template string."""
    if template_type == "projects":
        df = pd.DataFrame([
            {
                "Project Title": "Autonomous Campus Delivery Bot",
                "Project Type": "Major",
                "Team Size": 4,
                "Guide Email": "guide1@college.edu",
                "Semester": "Fall 2025",
                "Start Date": "2025-08-01",
                "Planned End Date": "2025-12-15"
            },
            {
                "Project Title": "AI Health Monitoring Wristband",
                "Project Type": "Minor",
                "Team Size": 3,
                "Guide Email": "guide2@college.edu",
                "Semester": "Fall 2025",
                "Start Date": "2025-08-01",
                "Planned End Date": "2025-12-15"
            }
        ])
    elif template_type == "reviews":
        df = pd.DataFrame([
            {
                "Project ID": 1,
                "Review Date": "2025-09-15",
                "Score": 18.5,
                "Reviewer Comment": "Good architecture diagram, on track."
            },
            {
                "Project ID": 2,
                "Review Date": "2025-09-15",
                "Score": 11.0,
                "Reviewer Comment": "Delayed implementation, missing key modules."
            }
        ])
    elif template_type == "progress":
        df = pd.DataFrame([
            {
                "Project ID": 1,
                "Week Start": "2025-08-15",
                "Completion Pct": 25.0,
                "Commits Or Updates": 8,
                "Deadline Slips": 0,
                "Missed Meetings": 0
            },
            {
                "Project ID": 2,
                "Week Start": "2025-08-15",
                "Completion Pct": 10.0,
                "Commits Or Updates": 1,
                "Deadline Slips": 1,
                "Missed Meetings": 1
            }
        ])
    else:
        df = pd.DataFrame()

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()
