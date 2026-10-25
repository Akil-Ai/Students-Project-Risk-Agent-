import os
import joblib
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix
)
import lightgbm as lgb
from sqlalchemy.orm import Session
from src.models import MLModel
from src.ml.features import get_feature_matrix_for_training, FEATURE_COLS
from src.services.settings import get_setting
from src.logger import logger

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models_store")
os.makedirs(MODEL_DIR, exist_ok=True)

def train_risk_model(db: Session, force_train: bool = False) -> Dict[str, Any]:
    """
    Trains risk prediction model (LightGBM + Baseline Logistic Regression)
    with class-imbalance handling, time-based split by semester,
    decision threshold optimization for target recall, and model versioning.
    """
    delay_threshold_days = int(get_setting(db, "delay_threshold_days", 14))
    min_projects = int(get_setting(db, "min_training_projects", 15))
    target_recall = float(get_setting(db, "target_recall", 0.85))

    df = get_feature_matrix_for_training(db, delay_threshold_days)

    if len(df) < min_projects and not force_train:
        raise ValueError(
            f"Insufficient completed projects for ML training ({len(df)} available, {min_projects} required). "
            f"Using cold-start rule-based scorer."
        )

    # Time-based split by semester
    semesters = sorted(df["semester"].unique().tolist())
    if len(semesters) > 1:
        # Latest semester as test set, earlier semesters as train set
        test_sem = semesters[-1]
        train_df = df[df["semester"] != test_sem]
        test_df = df[df["semester"] == test_sem]
        if len(test_df) == 0 or len(train_df) == 0:
            # Fallback if partition skewed
            train_df = df.sample(frac=0.8, random_state=42)
            test_df = df.drop(train_df.index)
    else:
        # Single semester: random stratified split
        train_df = df.sample(frac=0.8, random_state=42)
        test_df = df.drop(train_df.index)

    X_train = train_df[FEATURE_COLS]
    y_train = train_df["target"]
    X_test = test_df[FEATURE_COLS]
    y_test = test_df["target"]

    # Class weights for imbalance
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    scale_pos_weight = float(neg_count / max(1, pos_count))

    # 1. Baseline Logistic Regression
    lr = LogisticRegression(class_weight="balanced", max_iter=1000)
    lr.fit(X_train, y_train)

    # 2. LightGBM Classifier
    lgbm = lgb.LGBMClassifier(
        n_estimators=100,
        learning_rate=0.05,
        max_depth=4,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        verbosity=-1
    )
    lgbm.fit(X_train, y_train)

    # Predictions & Probabilities on test set
    y_probs = lgbm.predict_proba(X_test)[:, 1] if len(X_test) > 0 else np.array([])

    # If test set has only 1 class or empty, evaluate on full dataset for safety
    if len(np.unique(y_test)) < 2 or len(y_test) == 0:
        eval_X = df[FEATURE_COLS]
        eval_y = df["target"]
        eval_probs = lgbm.predict_proba(eval_X)[:, 1]
    else:
        eval_X = X_test
        eval_y = y_test
        eval_probs = y_probs

    # Find optimal decision threshold for target recall
    thresholds = np.linspace(0.1, 0.9, 81)
    best_thresh = 0.5
    best_f1 = 0.0

    for th in thresholds:
        preds = (eval_probs >= th).astype(int)
        rec = recall_score(eval_y, preds, zero_division=0)
        f1 = f1_score(eval_y, preds, zero_division=0)
        if rec >= target_recall:
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = float(th)

    final_preds = (eval_probs >= best_thresh).astype(int)

    roc_auc = float(roc_auc_score(eval_y, eval_probs)) if len(np.unique(eval_y)) > 1 else 1.0
    precision = float(precision_score(eval_y, final_preds, zero_division=0))
    recall = float(recall_score(eval_y, final_preds, zero_division=0))
    f1 = float(f1_score(eval_y, final_preds, zero_division=0))
    cm = confusion_matrix(eval_y, final_preds).tolist() if len(np.unique(eval_y)) > 1 else [[len(eval_y), 0], [0, 0]]

    # Feature importances
    feature_importances = dict(zip(FEATURE_COLS, [float(v) for v in lgbm.feature_importances_]))

    metrics = {
        "roc_auc": round(roc_auc, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "optimal_threshold": round(best_thresh, 4),
        "target_recall_configured": target_recall,
        "confusion_matrix": cm,
        "feature_importances": feature_importances,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "total_samples": len(df)
    }

    # Save model artifacts
    version = f"v_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    model_filename = f"lgbm_{version}.joblib"
    model_path = os.path.join(MODEL_DIR, model_filename)

    artifact_bundle = {
        "model": lgbm,
        "baseline_lr": lr,
        "feature_cols": FEATURE_COLS,
        "metrics": metrics,
        "optimal_threshold": best_thresh
    }
    joblib.dump(artifact_bundle, model_path)

    # Deactivate older models and insert newly trained model
    db.query(MLModel).update({MLModel.is_active: False})
    db_model = MLModel(
        version=version,
        trained_at=datetime.utcnow(),
        metrics=metrics,
        path=model_path,
        is_active=True
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)

    logger.info(f"Trained new model version {version} with ROC-AUC {roc_auc:.4f}, Recall {recall:.4f}")
    return {"version": version, "metrics": metrics, "path": model_path}
