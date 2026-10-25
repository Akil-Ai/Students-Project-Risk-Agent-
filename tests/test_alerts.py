import pytest
from datetime import datetime, date, timedelta
from src.db import engine, SessionLocal
from src.models import Base, Project, Alert, RiskScore
from src.services.alerts import check_and_generate_alerts_for_project, record_alert_feedback
from src.services.settings import sync_settings_from_config

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    sync_settings_from_config(session)
    yield session
    session.rollback()
    session.close()

def test_alert_high_risk_and_cooldown(db_session):
    # Create test project
    project = Project(
        title="Alert Testing Project",
        semester="Sem 8",
        start_date=date.today() - timedelta(days=60),
        planned_end_date=date.today() + timedelta(days=60),
        status="active"
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    # Insert a High risk score
    score1 = RiskScore(
        project_id=project.id,
        as_of_date=datetime.utcnow() - timedelta(minutes=5),
        probability=0.82,
        bucket="High",
        top_factors=[{"factor": "progress_gap", "impact": 0.4, "description": "Lags 30% behind"}]
    )
    db_session.add(score1)
    db_session.commit()

    # Check alert trigger
    alert = check_and_generate_alerts_for_project(db_session, project)
    assert alert is not None
    assert alert.type == "HIGH_RISK"
    assert alert.status == "open"
    assert "Lags 30% behind" in alert.reasons

    # Check cooldown suppression
    alert2 = check_and_generate_alerts_for_project(db_session, project)
    assert alert2 is None  # Should be suppressed by cooldown

    # Test feedback recording
    updated_alert = record_alert_feedback(db_session, alert.id, feedback="useful", new_status="resolved")
    assert updated_alert.feedback == "useful"
    assert updated_alert.status == "resolved"
