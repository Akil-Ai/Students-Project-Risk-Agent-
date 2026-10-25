import pytest
from src.ml.rules import score_with_rules

def test_score_with_rules_low_risk():
    features = {
        "progress_gap": 0.0,
        "days_since_last_update": 3.0,
        "action_item_closure_rate": 1.0,
        "missed_meetings_total": 0.0,
        "deadline_slips_count": 0.0,
        "comment_negative_flag": 0.0
    }
    settings = {
        "risk_bucket_low_max": 0.35,
        "risk_bucket_medium_max": 0.70,
        "rule_weights": {
            "progress_gap_weight": 0.30,
            "days_since_update_weight": 0.20,
            "action_item_closure_weight": 0.15,
            "missed_meetings_weight": 0.15,
            "deadline_slips_weight": 0.10,
            "negative_sentiment_weight": 0.10
        }
    }
    prob, bucket, top_factors = score_with_rules(features, settings)
    assert prob < 0.35
    assert bucket == "Low"
    assert len(top_factors) > 0

def test_score_with_rules_high_risk():
    features = {
        "progress_gap": 0.25,  # 25% behind
        "days_since_last_update": 25.0,  # 25 days stale
        "action_item_closure_rate": 0.20,  # low closure
        "missed_meetings_total": 3.0,  # 3 missed meetings
        "deadline_slips_count": 2.0,
        "comment_negative_flag": 2.0
    }
    settings = {
        "risk_bucket_low_max": 0.35,
        "risk_bucket_medium_max": 0.70,
        "rule_weights": {
            "progress_gap_weight": 0.30,
            "days_since_update_weight": 0.20,
            "action_item_closure_weight": 0.15,
            "missed_meetings_weight": 0.15,
            "deadline_slips_weight": 0.10,
            "negative_sentiment_weight": 0.10
        }
    }
    prob, bucket, top_factors = score_with_rules(features, settings)
    assert prob >= 0.70
    assert bucket == "High"
    # Triggered factors should include progress gap and stale updates
    factor_names = [f["factor"] for f in top_factors]
    assert "progress_gap" in factor_names or "days_since_last_update" in factor_names
