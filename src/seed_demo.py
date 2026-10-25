import argparse
import random
from datetime import date, timedelta
from src.db import init_db, SessionLocal
from src.models import (
    User, Guide, Student, Project, ProjectMember,
    Milestone, Review, ActionItem, ProgressLog
)
from src.services.auth import create_user, bootstrap_admin_if_empty
from src.services.settings import sync_settings_from_config
from src.services.risk import score_all_active_projects
from src.services.alerts import check_and_generate_alerts_all_active
from src.logger import logger

PROJECT_TOPICS = [
    ("Autonomous Drone for Disaster Surveillance", "Major"),
    ("Smart Grid Energy Distribution using IoT", "Major"),
    ("Deep Learning for Automated Retinal Disease Detection", "Capstone"),
    ("Blockchain-Based Academic Credential Verification", "Major"),
    ("Microservices Architecture for Hospital Management", "Minor"),
    ("AI-Powered Virtual Physics Laboratory", "Major"),
    ("Real-Time Traffic Optimization with Edge Computing", "Capstone"),
    ("Cyber Threat Hunting using Graph Neural Networks", "Major"),
    ("Voice Controlled Robotic Prosthetic Arm", "Major"),
    ("Secure Decentralized Voting Protocol", "Minor"),
    ("Predictive Maintenance for Industrial Machinery", "Major"),
    ("Federated Learning for Cross-Hospital Cancer Prognosis", "Capstone"),
    ("Multimodal Emotion Recognition in Video Calls", "Major"),
    ("Urban Air Quality Forecasting System", "Minor"),
    ("Automated Software Vulnerability Patching Bot", "Major")
]

POSITIVE_COMMENTS = [
    "Excellent design and proactive sprint completion. Team is ahead of schedule.",
    "Great progress on API integration. Code quality and tests are well maintained.",
    "Impressive demonstration of core functional modules. Highly responsive team."
]

NEGATIVE_COMMENTS = [
    "Delayed deliverables. The team is lagging significantly behind the planned schedule.",
    "Blocked on backend integration. Lack of progress and attendance was unsatisfactory.",
    "Multiple missed deadlines and poor communication. Immediate intervention needed."
]

def seed_database(num_projects: int = 30, num_semesters: int = 3):
    """Generates synthetic historical and active projects for demonstration and model training."""
    init_db()
    db = SessionLocal()
    try:
        sync_settings_from_config(db)
        admin = bootstrap_admin_if_empty(db)

        # 1. Create Guides
        logger.info("Creating demo Guides...")
        guides = []
        for i in range(1, 6):
            email = f"guide{i}@college.edu"
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                u = create_user(
                    db=db,
                    name=f"Dr. Faculty Guide {i}",
                    email=email,
                    password="Password@123",
                    role="guide",
                    department="Computer Science & Engineering"
                )
                guides.append(u.guide_profile)
            else:
                guides.append(existing.guide_profile)

        # 2. Create Students
        logger.info("Creating demo Students...")
        students = []
        for i in range(1, 41):
            email = f"student{i}@college.edu"
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                u = create_user(
                    db=db,
                    name=f"Student Scholar {i}",
                    email=email,
                    password="Password@123",
                    role="student",
                    usn_or_roll=f"1MS22CS{i:03d}",
                    batch_year=2026
                )
                students.append(u.student_profile)
            else:
                students.append(existing.student_profile)

        # 3. Create Projects across semesters
        semester_names = [f"Semester {7 - s} (202{4+s})" for s in range(num_semesters)]
        # Make the latest semester the active one
        active_semester = semester_names[-1]

        logger.info(f"Generating {num_projects} projects across {num_semesters} semesters...")

        proj_count = 0
        for s_idx, sem in enumerate(semester_names):
            is_active_sem = (sem == active_semester)
            # Allocate projects per semester
            projects_in_sem = num_projects // num_semesters
            if s_idx == num_semesters - 1:
                projects_in_sem += num_projects % num_semesters

            for p_i in range(projects_in_sem):
                proj_count += 1
                topic, ptype = random.choice(PROJECT_TOPICS)
                title = f"{topic} (Group {proj_count})"
                guide = random.choice(guides)

                if is_active_sem:
                    # Active project
                    start_d = date.today() - timedelta(days=random.randint(30, 90))
                    planned_end = start_d + timedelta(days=120)
                    actual_end = None
                    status = "active"
                    # Determine whether this active project will be at high risk
                    will_struggle = (p_i % 3 == 0)
                else:
                    # Completed project
                    start_d = date(2024, 1, 10) + timedelta(days=s_idx * 150 + p_i * 2)
                    planned_end = start_d + timedelta(days=120)
                    status = "completed"
                    # 40% completed projects were delayed
                    was_delayed = (p_i % 5 in [0, 1])
                    delay_days = random.randint(18, 45) if was_delayed else random.randint(-10, 5)
                    actual_end = planned_end + timedelta(days=delay_days)
                    will_struggle = was_delayed

                proj = Project(
                    title=title,
                    type=ptype,
                    team_size=3,
                    guide_id=guide.id,
                    semester=sem,
                    start_date=start_d,
                    planned_end_date=planned_end,
                    actual_end_date=actual_end,
                    status=status
                )
                db.add(proj)
                db.flush()

                # Assign 2-3 students
                assigned_students = random.sample(students, min(3, len(students)))
                for st in assigned_students:
                    pm = ProjectMember(project_id=proj.id, student_id=st.id)
                    db.add(pm)

                # Add Milestones
                ms_defs = [
                    ("Requirement Analysis & System Architecture", 0.25, 30),
                    ("Core Module Prototype Implementation", 0.50, 60),
                    ("Integration & System Validation", 0.75, 90),
                    ("Final Deployment, Report & Defense", 1.00, 120)
                ]
                for ms_name, planned_pct, day_offset in ms_defs:
                    ms_date = start_d + timedelta(days=day_offset)
                    comp_date = None
                    if status == "completed":
                        comp_date = ms_date + (timedelta(days=random.randint(5, 20)) if will_struggle else timedelta(days=random.randint(-5, 0)))
                    elif is_active_sem and ms_date < date.today():
                        comp_date = ms_date if not will_struggle else None

                    ms = Milestone(
                        project_id=proj.id,
                        name=ms_name,
                        planned_date=ms_date,
                        planned_pct=planned_pct * 100.0,
                        completed_date=comp_date
                    )
                    db.add(ms)

                # Add Reviews
                review_dates = [start_d + timedelta(days=35), start_d + timedelta(days=70)]
                for r_idx, r_date in enumerate(review_dates):
                    if r_date > (actual_end or date.today()):
                        continue
                    if will_struggle:
                        score = random.uniform(9.0, 13.0)
                        comm = random.choice(NEGATIVE_COMMENTS)
                    else:
                        score = random.uniform(16.0, 20.0)
                        comm = random.choice(POSITIVE_COMMENTS)

                    rev = Review(
                        project_id=proj.id,
                        review_date=r_date,
                        rubric_scores={"methodology": score * 0.4, "implementation": score * 0.4, "viva": score * 0.2, "total": score},
                        attendance=0.7 if will_struggle else 1.0,
                        reviewer_comment=comm,
                        action_items_summary="Resolve sprint blockers" if will_struggle else "Maintain velocity"
                    )
                    db.add(rev)
                    db.flush()

                    # Add Action Item
                    ai_status = "pending" if (will_struggle and is_active_sem) else ("completed" if not will_struggle else "overdue")
                    ai = ActionItem(
                        review_id=rev.id,
                        project_id=proj.id,
                        description="Submit architecture review & fix pending database schema" if will_struggle else "Complete unit tests",
                        due_date=r_date + timedelta(days=14),
                        status=ai_status
                    )
                    db.add(ai)

                # Add Progress Logs
                curr_w = start_d
                eval_limit = actual_end or date.today()
                w_count = 0
                cum_pct = 0.0

                while curr_w <= eval_limit:
                    w_count += 1
                    if will_struggle:
                        step_pct = random.uniform(2.0, 5.0)
                        updates = random.randint(0, 2)
                        missed_m = 1 if (w_count % 2 == 0) else 0
                        slips = 1 if (w_count % 3 == 0) else 0
                    else:
                        step_pct = random.uniform(8.0, 14.0)
                        updates = random.randint(5, 12)
                        missed_m = 0
                        slips = 0

                    cum_pct = min(100.0, cum_pct + step_pct)
                    pl = ProgressLog(
                        project_id=proj.id,
                        week_start=curr_w,
                        milestone_completion_pct=cum_pct,
                        commits_or_updates=updates,
                        missed_meetings=missed_m,
                        deadline_slips=slips,
                        notes="Weekly sync update."
                    )
                    db.add(pl)
                    curr_w += timedelta(days=7)

        db.commit()
        logger.info("Successfully seeded synthetic demo data.")

        # Score active projects and generate alerts
        logger.info("Scoring active projects and evaluating initial alerts...")
        score_all_active_projects(db)
        check_and_generate_alerts_all_active(db)
        logger.info("Initial scoring and alerting complete.")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo data for Student Project Risk Agent")
    parser.add_argument("--projects", type=int, default=30, help="Total projects to generate")
    parser.add_argument("--semesters", type=int, default=3, help="Number of semesters to span")
    args = parser.parse_args()
    seed_database(num_projects=args.projects, num_semesters=args.semesters)
