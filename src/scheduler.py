from apscheduler.schedulers.background import BackgroundScheduler
from src.db import SessionLocal
from src.services.settings import get_setting
from src.services.risk import score_all_active_projects
from src.services.alerts import check_and_generate_alerts_all_active
from src.logger import logger

scheduler = BackgroundScheduler()

def scheduled_risk_and_alert_job():
    """Periodic job executed by APScheduler to re-score active projects and fire alerts."""
    logger.info("Executing scheduled project risk evaluation job...")
    db = SessionLocal()
    try:
        scored = score_all_active_projects(db)
        alerts = check_and_generate_alerts_all_active(db)
        logger.info(f"Scheduled job completed: Scored {len(scored)} active projects, generated {len(alerts)} alerts.")
    except Exception as e:
        logger.error(f"Error in scheduled risk evaluation: {e}")
    finally:
        db.close()

def start_scheduler():
    """Initializes and starts the background scheduler with interval from settings."""
    if scheduler.running:
        return
    db = SessionLocal()
    try:
        interval_min = int(get_setting(db, "scheduler_interval_minutes", 60))
    finally:
        db.close()

    scheduler.add_job(
        scheduled_risk_and_alert_job,
        trigger="interval",
        minutes=interval_min,
        id="risk_scoring_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Started background APScheduler running every {interval_min} minutes.")

def stop_scheduler():
    """Stops the scheduler if running."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Stopped background APScheduler.")
