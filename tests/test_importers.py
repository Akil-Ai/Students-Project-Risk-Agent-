import pytest
import pandas as pd
from datetime import date
from src.db import engine, SessionLocal
from src.models import Base, Project
from src.importers import import_projects_dataframe, generate_csv_template

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def test_generate_csv_template():
    tmpl = generate_csv_template("projects")
    assert "Project Title" in tmpl
    assert "Planned End Date" in tmpl

def test_import_projects_dataframe(db_session):
    data = [
        {"Title": "Imported Test Project A", "Sem": "Fall 2025", "PlannedEnd": "2025-12-20", "Type": "Major", "Size": 4},
        {"Title": "", "Sem": "Fall 2025", "PlannedEnd": "2025-12-20", "Type": "Major", "Size": 4}, # Invalid: empty title
        {"Title": "Imported Test Project B", "Sem": "Fall 2025", "PlannedEnd": "invalid-date", "Type": "Minor", "Size": 3} # Invalid date
    ]
    df = pd.DataFrame(data)
    mapping = {
        "Title": "title",
        "Sem": "semester",
        "PlannedEnd": "planned_end_date",
        "Type": "type",
        "Size": "team_size"
    }

    success_count, errors = import_projects_dataframe(db_session, df, mapping)
    assert success_count == 1
    assert len(errors) == 2
    assert errors[0]["error"] == "Missing project title"
    assert "planned_end_date" in errors[1]["error"]

    # Verify saved
    p = db_session.query(Project).filter(Project.title == "Imported Test Project A").first()
    assert p is not None
    assert p.semester == "Fall 2025"
