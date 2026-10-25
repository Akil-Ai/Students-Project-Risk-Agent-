from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from src.services.settings import get_setting

def score_with_rules(features: Dict[str, float], settings_dict: Dict[str, Any]) -> Tuple[float, str, List[Dict[str, Any]]]:
    """
    Cold-start rule-based heuristic risk scoring.
    Computes a risk probability in [0, 1], assigns a risk bucket, and returns triggered rules.
    """
    rule_weights = settings_dict.get("rule_weights", {})
    if isinstance(rule_weights, str):
        try:
            import json
            rule_weights = json.loads(rule_weights)
        except Exception:
            rule_weights = {}

    if not isinstance(rule_weights, dict) or not rule_weights:
        rule_weights = {
            "progress_gap_weight": 0.30,
            "days_since_update_weight": 0.20,
            "action_item_closure_weight": 0.15,
            "missed_meetings_weight": 0.15,
            "deadline_slips_weight": 0.10,
            "negative_sentiment_weight": 0.10
        }


    # Sub-component risk scores (each normalized 0.0 - 1.0)
    # 1. Progress gap: > 0 means behind. 25% behind = 1.0 risk
    gap = features.get("progress_gap", 0.0)
    r_gap = max(0.0, min(1.0, gap / 0.25))

    # 2. Days since update: 21+ days without update = 1.0 risk
    days_stale = features.get("days_since_last_update", 0.0)
    r_stale = max(0.0, min(1.0, days_stale / 21.0))

    # 3. Action item closure rate: 0% closed = 1.0 risk, 100% closed = 0.0 risk
    closure = features.get("action_item_closure_rate", 1.0)
    r_closure = 1.0 - max(0.0, min(1.0, closure))

    # 4. Missed meetings: 3+ missed = 1.0 risk
    missed = features.get("missed_meetings_total", 0.0)
    r_missed = max(0.0, min(1.0, missed / 3.0))

    # 5. Deadline slips: 2+ slips = 1.0 risk
    slips = features.get("deadline_slips_count", 0.0)
    r_slips = max(0.0, min(1.0, slips / 2.0))

    # 6. Negative comment flags: 2+ negative flags = 1.0 risk
    neg_flags = features.get("comment_negative_flag", 0.0)
    r_neg = max(0.0, min(1.0, neg_flags / 2.0))

    # Weighted probability
    w_sum = sum(rule_weights.values()) or 1.0
    prob = (
        r_gap * rule_weights.get("progress_gap_weight", 0.30) +
        r_stale * rule_weights.get("days_since_update_weight", 0.20) +
        r_closure * rule_weights.get("action_item_closure_weight", 0.15) +
        r_missed * rule_weights.get("missed_meetings_weight", 0.15) +
        r_slips * rule_weights.get("deadline_slips_weight", 0.10) +
        r_neg * rule_weights.get("negative_sentiment_weight", 0.10)
    ) / w_sum

    prob = round(max(0.0, min(1.0, prob)), 4)

    # Determine bucket based on settings
    low_max = float(settings_dict.get("risk_bucket_low_max", 0.35))
    med_max = float(settings_dict.get("risk_bucket_medium_max", 0.70))

    if prob < low_max:
        bucket = "Low"
    elif prob < med_max:
        bucket = "Medium"
    else:
        bucket = "High"

    # Identify triggered rules / top factors
    top_factors = []
    if gap > 0.05:
        top_factors.append({
            "factor": "progress_gap",
            "impact": round(r_gap * rule_weights.get("progress_gap_weight", 0.30), 3),
            "description": f"Progress gap of {gap:.1%} behind planned milestones"
        })
    if days_stale >= 10:
        top_factors.append({
            "factor": "days_since_last_update",
            "impact": round(r_stale * rule_weights.get("days_since_update_weight", 0.20), 3),
            "description": f"No progress updates logged for {days_stale:.0f} days"
        })
    if closure < 0.70:
        top_factors.append({
            "factor": "action_item_closure_rate",
            "impact": round(r_closure * rule_weights.get("action_item_closure_weight", 0.15), 3),
            "description": f"Low action item completion rate of {closure:.1%}"
        })
    if missed > 0:
        top_factors.append({
            "factor": "missed_meetings_total",
            "impact": round(r_missed * rule_weights.get("missed_meetings_weight", 0.15), 3),
            "description": f"{missed:.0f} missed team/guide meetings"
        })
    if slips > 0:
        top_factors.append({
            "factor": "deadline_slips_count",
            "impact": round(r_slips * rule_weights.get("deadline_slips_weight", 0.10), 3),
            "description": f"{slips:.0f} milestone deadline slips recorded"
        })
    if neg_flags > 0:
        top_factors.append({
            "factor": "comment_negative_flag",
            "impact": round(r_neg * rule_weights.get("negative_sentiment_weight", 0.10), 3),
            "description": f"Critical concern/friction flags in guide review comments"
        })

    # Sort factors by impact
    top_factors.sort(key=lambda x: x["impact"], reverse=True)
    if not top_factors:
        top_factors.append({
            "factor": "steady_progress",
            "impact": 0.0,
            "description": "Project is advancing on track with steady updates"
        })

    return prob, bucket, top_factors[:3]
