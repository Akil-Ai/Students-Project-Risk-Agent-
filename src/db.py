import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from src.models import Base
from src.logger import logger

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
LEXICON_PATH = BASE_DIR / "config" / "lexicon.yaml"

# Load base YAML config
def load_yaml_config():
    if not CONFIG_PATH.exists():
        logger.warning(f"Config file not found at {CONFIG_PATH}, using defaults.")
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_lexicon_config():
    if not LEXICON_PATH.exists():
        return {"negative_keywords": [], "positive_keywords": []}
    with open(LEXICON_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

# Database URL from env with SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/project_agent.db")

# Ensure directory for sqlite db exists
if DATABASE_URL.startswith("sqlite:///"):
    sqlite_path = DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(os.path.abspath(sqlite_path)), exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False
)

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes schema and synchronizes base config with settings table."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
