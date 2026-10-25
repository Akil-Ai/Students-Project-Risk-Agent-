import pytest
from src.db import engine, SessionLocal
from src.models import Base, User
from src.services.auth import create_user, authenticate_user, hash_password, verify_password, bootstrap_admin_if_empty

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def test_password_hashing():
    pw = "Secret@123"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("Wrong@123", hashed) is False

def test_user_creation_and_auth(db_session):
    email = "test_guide@college.edu"
    existing = db_session.query(User).filter(User.email == email).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    user = create_user(
        db=db_session,
        name="Dr. Testing Guide",
        email=email,
        password="Password@123",
        role="guide",
        department="Computer Science"
    )
    assert user.id is not None
    assert user.role == "guide"
    assert user.guide_profile is not None
    assert user.guide_profile.department == "Computer Science"

    auth_user = authenticate_user(db_session, email, "Password@123")
    assert auth_user is not None
    assert auth_user.id == user.id

    bad_auth = authenticate_user(db_session, email, "WrongPassword")
    assert bad_auth is None

def test_bootstrap_admin(db_session):
    admin = bootstrap_admin_if_empty(db_session)
    assert admin is not None
    assert admin.role == "admin"
