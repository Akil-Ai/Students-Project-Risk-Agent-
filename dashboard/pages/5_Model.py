import streamlit as st
import pandas as pd
import plotly.express as px
from src.db import SessionLocal
from src.models import MLModel, Project, User
from src.ml.train import train_risk_model
from src.services.settings import get_setting
from dashboard.components import apply_custom_styles, render_metric_card

st.set_page_config(page_title="Model Management | Risk Agent", page_icon="🤖", layout="wide")
apply_custom_styles()

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the Login page first.")
    st.stop()

db = SessionLocal()
try:
    current_user = db.query(User).filter(User.id == st.session_state["user_id"]).first()
    if current_user.role != "admin":
        st.error("Model management and retraining is restricted to Administrators.")
        st.stop()

    st.title("🤖 ML Model Management & Retraining")
    st.markdown("Manage LightGBM classification models, evaluate validation metrics, and train updated versions.")

    # Completed projects check
    completed_count = db.query(Project).filter(Project.status == "completed").count()
    min_required = int(get_setting(db, "min_training_projects", 15))

    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card("Completed Training Projects", str(completed_count), f"Minimum required: {min_required}")
    with c2:
        active_model = db.query(MLModel).filter(MLModel.is_active == True).first()
        render_metric_card("Active Model Version", active_model.version if active_model else "Rule-Based Heuristic")
    with c3:
        target_rec = float(get_setting(db, "target_recall", 0.85))
        render_metric_card("Target Recall Policy", f"{target_rec:.0%}", "Configured in Settings")

    st.markdown("---")

    # Retrain button
    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        if st.button("🚀 Retrain LightGBM Model Now", type="primary", use_container_width=True):
            with st.spinner("Training model with class-imbalance weights and semester split..."):
                try:
                    res = train_risk_model(db, force_train=(completed_count >= 5))
                    st.success(f"Successfully trained model version: {res['version']}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Retraining error: {e}")

    with col_info:
        st.caption("ℹ️ Retraining partitions historical completed projects by semester, tunes the decision threshold to satisfy target recall, and generates SHAP explainability artifacts.")

    # Active Model Evaluation Metrics
    if active_model and isinstance(active_model.metrics, dict):
        m = active_model.metrics
        st.subheader(f"📊 Active Model Evaluation ({active_model.version})")

        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric("ROC-AUC", f"{m.get('roc_auc', 0.0):.3f}")
        with m_col2:
            st.metric("Recall", f"{m.get('recall', 0.0):.1%}")
        with m_col3:
            st.metric("Precision", f"{m.get('precision', 0.0):.1%}")
        with m_col4:
            st.metric("Optimal Threshold", f"{m.get('optimal_threshold', 0.5):.2f}")

        # Feature Importance Chart
        if "feature_importances" in m:
            st.subheader("Feature Importance (Split Gain)")
            fi_df = pd.DataFrame([
                {"Feature": k, "Importance": v} for k, v in m["feature_importances"].items()
            ]).sort_values("Importance", ascending=True)

            fig_fi = px.bar(fi_df, x="Importance", y="Feature", orientation="h", title="LightGBM Feature Importance")
            st.plotly_chart(fig_fi, use_container_width=True)

        # Confusion Matrix
        if "confusion_matrix" in m:
            st.subheader("Confusion Matrix")
            cm = m["confusion_matrix"]
            cm_df = pd.DataFrame(
                cm,
                index=["Actual On-Time", "Actual Delayed"],
                columns=["Pred On-Time", "Pred Delayed"]
            )
            st.table(cm_df)

    # Model Version History
    st.subheader("📜 Version History")
    all_models = db.query(MLModel).order_by(MLModel.trained_at.desc()).all()
    if all_models:
        for mod in all_models:
            col_v1, col_v2, col_v3 = st.columns([2, 2, 1])
            with col_v1:
                st.markdown(f"**Version:** `{mod.version}` {'(ACTIVE)' if mod.is_active else ''}")
                st.caption(f"Trained: {mod.trained_at.strftime('%Y-%m-%d %H:%M')}")
            with col_v2:
                roc = mod.metrics.get("roc_auc", "N/A")
                rec = mod.metrics.get("recall", "N/A")
                st.markdown(f"ROC-AUC: **{roc}** | Recall: **{rec}**")
            with col_v3:
                if not mod.is_active:
                    if st.button("Activate", key=f"activate_{mod.id}"):
                        db.query(MLModel).update({MLModel.is_active: False})
                        mod.is_active = True
                        db.commit()
                        st.success(f"Activated {mod.version}")
                        st.rerun()

finally:
    db.close()
