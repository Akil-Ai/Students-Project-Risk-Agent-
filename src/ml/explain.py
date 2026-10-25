import os
import joblib
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import shap
from src.services.settings import get_setting

FEATURE_COLS = [
    "progress_gap",
    "action_item_closure_rate",
    "commit_update_trend",
    "days_since_last_update",
    "missed_meetings_total",
    "deadline_slips_count",
    "rubric_score_trend",
    "comment_negative_flag",
    "guide_workload",
    "semester_week"
]

def explain_prediction_shap(
    model: Any,
    feature_row: pd.DataFrame,
    explainer: Optional[Any] = None,
    templates: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Computes SHAP values for a single feature vector and formats top-3 positive contributors
    into human-friendly plain English descriptions using config templates.
    """
    if templates is None:
        templates = {
            "progress_gap": "Project progress lags {value:.1%} behind planned milestones.",
            "days_since_last_update": "No progress updates or commits logged for {value:.0f} days.",
            "action_item_closure_rate": "Action item closure rate is critically low at {value:.1%}.",
            "missed_meetings_total": "{value:.0f} project meetings were missed recently.",
            "deadline_slips_count": "{value:.0f} milestone deadline slip(s) recorded.",
            "comment_negative_flag": "Review comments reflect critical concerns and blockers.",
            "rubric_score_trend": "Review performance scores have declined over recent evaluations.",
            "guide_workload": "Guide is currently mentoring {value:.0f} active projects."
        }

    try:
        if explainer is None:
            explainer = shap.TreeExplainer(model)
        
        shap_vals = explainer.shap_values(feature_row)
        # Handle binary classification output format differences in SHAP versions
        if isinstance(shap_vals, list):
            sv = shap_vals[1][0] if len(shap_vals) > 1 else shap_vals[0][0]
        elif isinstance(shap_vals, np.ndarray) and len(shap_vals.shape) == 3:
            sv = shap_vals[0, :, 1]
        elif isinstance(shap_vals, np.ndarray) and len(shap_vals.shape) == 2:
            sv = shap_vals[0]
        else:
            sv = shap_vals

        factors = []
        for col_name, shap_impact in zip(feature_row.columns, sv):
            feat_val = float(feature_row[col_name].iloc[0])
            # Format text using template
            tmpl = templates.get(col_name)
            if tmpl:
                try:
                    desc = tmpl.format(value=feat_val)
                except Exception:
                    desc = f"{col_name}: {feat_val:.2f}"
            else:
                desc = f"{col_name}: {feat_val:.2f}"

            factors.append({
                "factor": col_name,
                "impact": float(shap_impact),
                "value": feat_val,
                "description": desc
            })

        # Sort by positive SHAP impact (features driving risk UP)
        factors.sort(key=lambda x: x["impact"], reverse=True)
        return factors[:3]
    except Exception as e:
        # Fallback if SHAP computation fails
        fallback_factors = []
        for col in feature_row.columns:
            fallback_factors.append({
                "factor": col,
                "impact": 0.0,
                "description": f"{col}: {feature_row[col].iloc[0]}"
            })
        return fallback_factors[:3]
