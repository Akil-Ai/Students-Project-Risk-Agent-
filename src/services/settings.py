import json
from typing import Any, Dict
from sqlalchemy.orm import Session
from src.models import Setting
from src.db import load_yaml_config
from src.logger import logger

def sync_settings_from_config(db: Session) -> None:
    """Syncs default settings from config.yaml into the settings DB table if missing."""
    config = load_yaml_config()
    
    defaults = {
        "delay_threshold_days": (str(config.get("delay_threshold_days", 14)), "Days past planned end date before project is labeled delayed"),
        "min_training_projects": (str(config.get("min_training_projects", 15)), "Minimum completed projects required to train ML model"),
        "target_recall": (str(config.get("target_recall", 0.85)), "Target recall for model decision threshold tuning"),
        "jump_threshold": (str(config.get("jump_threshold", 0.20)), "Week-over-week risk jump to trigger an alert"),
        "alert_cooldown_days": (str(config.get("alert_cooldown_days", 7)), "Days to suppress duplicate alerts for the same project"),
        "risk_bucket_low_max": (str(config.get("risk_buckets", {}).get("low_max", 0.35)), "Risk threshold separating Low and Medium buckets"),
        "risk_bucket_medium_max": (str(config.get("risk_buckets", {}).get("medium_max", 0.70)), "Risk threshold separating Medium and High buckets"),
        "rule_weights": (json.dumps(config.get("rule_weights", {})), "JSON dictionary of rule weights for cold-start heuristic scoring"),
        "suggested_actions": (json.dumps(config.get("suggested_actions", {})), "JSON dictionary of suggested intervention actions"),
        "explanation_templates": (json.dumps(config.get("explanation_templates", {})), "JSON dictionary of plain-English explanation templates"),
        "scheduler_interval_minutes": (str(config.get("scheduler", {}).get("risk_scoring_interval_minutes", 60)), "Scheduler periodic scoring interval in minutes")
    }

    for key, (val, desc) in defaults.items():
        existing = db.query(Setting).filter(Setting.key == key).first()
        if not existing:
            setting = Setting(key=key, value=val, description=desc)
            db.add(setting)
    db.commit()

def get_setting(db: Session, key: str, default: Any = None) -> Any:
    """Retrieves a setting value, parsing numbers/JSON when appropriate."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if not setting:
        return default
    raw_val = setting.value
    # Try parsing json / int / float
    try:
        if raw_val.startswith("{") or raw_val.startswith("["):
            return json.loads(raw_val)
        if "." in raw_val:
            return float(raw_val)
        return int(raw_val)
    except (ValueError, TypeError, json.JSONDecodeError):
        return raw_val

def get_all_settings(db: Session) -> Dict[str, Dict[str, Any]]:
    """Returns all settings with their values and descriptions."""
    items = db.query(Setting).all()
    res = {}
    for item in items:
        res[item.key] = {
            "value": item.value,
            "description": item.description,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None
        }
    return res

def update_setting(db: Session, key: str, value: Any, description: str = None) -> Setting:
    """Updates or creates a setting."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
    if not setting:
        setting = Setting(key=key, value=val_str, description=description)
        db.add(setting)
    else:
        setting.value = val_str
        if description:
            setting.description = description
    db.commit()
    db.refresh(setting)
    logger.info(f"Updated setting '{key}' = {val_str}")
    return setting
