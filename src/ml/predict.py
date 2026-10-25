import os
import joblib
from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from src.models import MLModel, Project
from src.ml.features import extract_project_features, FEATURE_COLS
from src.ml.rules import score_with_rules
from src.ml.explain import explain_prediction_shap
from src.services.settings import get_all_settings
from src.logger import logger

def predict_project_risk(db: Session, project: Project) -> Dict[str, Any]:
    """
    Predicts risk for a single project.
    Determines whether to use active ML model or fallback to cold-start rules.
    Returns:
        probability: float [0, 1]
        bucket: "Low" | "Medium" | "High"
        top_factors: list of top risk factors with plain English descriptions
        model_version: str ("rule-based" or model version name)
    """
    settings_dict = {k: v["value"] for k, v in get_all_settings(db).items()}
    low_max = float(settings_dict.get("risk_bucket_low_max", 0.35))
    med_max = float(settings_dict.get("risk_bucket_medium_max", 0.70))

    # Extract features
    features = extract_project_features(db, project)

    # Check for active ML model
    active_model_record = db.query(MLModel).filter(MLModel.is_active == True).first()

    if active_model_record and os.path.exists(active_model_record.path):
        try:
            bundle = joblib.load(active_model_record.path)
            model = bundle["model"]
            feat_df = pd.DataFrame([features])[FEATURE_COLS]
            
            # Predict probability
            prob = float(model.predict_proba(feat_df)[0][1])
            prob = round(max(0.0, min(1.0, prob)), 4)

            # Assign bucket
            if prob < low_max:
                bucket = "Low"
            elif prob < med_max:
                bucket = "Medium"
            else:
                bucket = "High"

            # Compute SHAP explanations
            top_factors = explain_prediction_shap(model, feat_df)

            return {
                "probability": prob,
                "bucket": bucket,
                "top_factors": top_factors,
                "model_version": active_model_record.version,
                "features": features
            }
        except Exception as e:
            logger.warning(f"Error predicting with ML model {active_model_record.version}: {e}. Falling back to rules.")

    # Cold start rule-based scorer
    prob, bucket, top_factors = score_with_rules(features, settings_dict)
    return {
        "probability": prob,
        "bucket": bucket,
        "top_factors": top_factors,
        "model_version": "rule-based",
        "features": features
    }
