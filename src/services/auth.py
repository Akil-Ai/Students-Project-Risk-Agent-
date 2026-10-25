import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models import User, Guide, Student, AuditLog
from src.logger import logger

def hash_password(password: str) -> str:
    """Hashes a password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticates a user by email and password."""
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def create_user(
    db: Session,
    name: str,
    email: str,
    password: str,
    role: str = "student",
    department: str = "Computer Science",
    usn_or_roll: str = None,
    batch_year: int = 2026,
    creator_id: Optional[int] = None
) -> User:
    """Creates a new user and role-specific profile (Guide or Student)."""
    normalized_email = email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise ValueError(f"User with email {email} already exists.")

    hashed = hash_password(password)
    user = User(
        name=name.strip(),
        email=normalized_email,
        password_hash=hashed,
        role=role.lower()
    )
    db.add(user)
    db.flush()

    if role.lower() == "guide":
        guide = Guide(user_id=user.id, department=department)
        db.add(guide)
    elif role.lower() == "student":
        roll = usn_or_roll or f"USN{user.id:04d}"
        student = Student(user_id=user.id, usn_or_roll=roll, batch_year=batch_year)
        db.add(student)

    # Audit log
    audit = AuditLog(
        user_id=creator_id or user.id,
        action="CREATE_USER",
        details={"created_user_id": user.id, "email": user.email, "role": user.role}
    )
    db.add(audit)
    db.commit()
    db.refresh(user)
    logger.info(f"Created user {user.email} with role {user.role}")
    return user

def bootstrap_admin_if_empty(db: Session) -> Optional[User]:
    """Creates an initial administrator if no admin user exists, using .env credentials."""
    admin = db.query(User).filter(User.role == "admin").first()
    if not admin:
        admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@college.edu")
        admin_pass = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin@123456")
        admin_name = os.getenv("INITIAL_ADMIN_NAME", "System Administrator")
        logger.info(f"Bootstrapping initial admin user: {admin_email}")
        admin = create_user(
            db=db,
            name=admin_name,
            email=admin_email,
            password=admin_pass,
            role="admin"
        )
    return admin
