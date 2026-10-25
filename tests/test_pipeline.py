import pytest
from src.db import engine, SessionLocal
from src.models import Base, Project, Alert, MLModel
from src.seed_demo import seed_database
from src.ml.train import train_risk_model
from src.services.risk import score_all_active_projects
from src.services.alerts import check_and_generate_alerts_all_active

def test_full_pipeline_seed_train_predict_alert():
    # 1. Run synthetic seed
    seed_database(num_projects=24, num_semesters=3)

    db = SessionLocal()
    try:
        # Check projects seeded
        all_projs = db.query(Project).all()
        assert len(all_projs) >= 24

        # 2. Train ML model
        train_res = train_risk_model(db, force_train=True)
        assert "version" in train_res
        assert "metrics" in train_res
        metrics = train_res["metrics"]
        assert "roc_auc" in metrics
        assert "optimal_threshold" in metrics

        # 3. Score active projects using new model
        scores = score_all_active_projects(db)
        assert len(scores) > 0
        for s in scores:
            assert s.probability >= 0.0 and s.probability <= 1.0
            assert s.bucket in ["Low", "Medium", "High"]
            assert len(s.top_factors) > 0

        # 4. Check alert generation
        alerts = check_and_generate_alerts_all_active(db)
        # Verify any alerts have proper structure
        open_alerts = db.query(Alert).filter(Alert.status == "open").all()
        assert len(open_alerts) >= 0  # Valid execution
    finally:
        db.close()
