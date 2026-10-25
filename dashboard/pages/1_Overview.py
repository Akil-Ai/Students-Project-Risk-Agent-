import streamlit as st
import pandas as pd
from src.db import SessionLocal
from src.models import User, Project, Alert, MLModel
from src.services.projects import list_projects_for_user
from src.services.risk import get_latest_risk_for_project
from dashboard.components import apply_custom_styles, render_metric_card, render_empty_state, render_risk_badge

st.set_page_config(page_title="Overview | Project Risk Agent", page_icon="📊", layout="wide")
apply_custom_styles()

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the main Login page first.")
    st.stop()

db = SessionLocal()
try:
    current_user = db.query(User).filter(User.id == st.session_state["user_id"]).first()
    projects = list_projects_for_user(db, current_user)

    st.title("📊 Project Progress & Risk Overview")
    st.markdown(f"Real-time overview for **{current_user.name}** ({current_user.role.title()})")

    if not projects:
        render_empty_state(
            title="No Projects Found",
            description="You do not have any projects assigned yet. Use the Data Import page or Admin panel to add projects."
        )
        st.stop()

    # Pre-fetch latest risk for each project
    project_rows = []
    high_risk_count = 0
    medium_risk_count = 0
    low_risk_count = 0

    for p in projects:
        risk = get_latest_risk_for_project(db, p.id)
        bucket = risk.bucket if risk else "Unscored"
        prob = risk.probability if risk else 0.0
        factors = risk.top_factors if risk else []
        model_ver = risk.model_version if risk else "None"

        if bucket == "High":
            high_risk_count += 1
        elif bucket == "Medium":
            medium_risk_count += 1
        elif bucket == "Low":
            low_risk_count += 1

        top_desc = factors[0].get("description", "-") if factors else "-"

        project_rows.append({
            "ID": p.id,
            "Title": p.title,
            "Type": p.type,
            "Semester": p.semester,
            "Status": p.status.title(),
            "Guide": p.guide.user.name if p.guide and p.guide.user else "Unassigned",
            "Risk Bucket": bucket,
            "Delay Probability": f"{prob:.1%}" if risk else "N/A",
            "Top Risk Driver": top_desc,
            "Model Version": model_ver
        })

    # KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_metric_card("Total Monitored Projects", str(len(projects)), "Across all active semesters")
    with k2:
        render_metric_card("High Risk (Urgent Action)", str(high_risk_count), "Predicted severe completion delay")
    with k3:
        render_metric_card("Medium Risk (At Watch)", str(medium_risk_count), "Mild milestone or attendance lags")
    with k4:
        render_metric_card("Low Risk (On Track)", str(low_risk_count), "Meeting scheduled milestones")

    st.markdown("---")

    # Filters
    f1, f2, f3 = st.columns(3)
    df = pd.DataFrame(project_rows)

    with f1:
        semesters = ["All"] + sorted(list(df["Semester"].unique()))
        sel_sem = st.selectbox("Filter by Semester", semesters)
    with f2:
        types = ["All"] + sorted(list(df["Type"].unique()))
        sel_type = st.selectbox("Filter by Project Type", types)
    with f3:
        buckets = ["All", "High", "Medium", "Low", "Unscored"]
        sel_bucket = st.selectbox("Filter by Risk Bucket", buckets)

    # Apply filters
    filtered_df = df.copy()
    if sel_sem != "All":
        filtered_df = filtered_df[filtered_df["Semester"] == sel_sem]
    if sel_type != "All":
        filtered_df = filtered_df[filtered_df["Type"] == sel_type]
    if sel_bucket != "All":
        filtered_df = filtered_df[filtered_df["Risk Bucket"] == sel_bucket]

    # Display Table
    st.subheader(f"Monitored Projects ({len(filtered_df)})")
    st.dataframe(
        filtered_df,
        column_config={
            "Delay Probability": st.column_config.ProgressColumn(
                "Delay Probability",
                help="Predicted probability of missing final project deadline",
                format="%.1f%%",
                min_value=0.0,
                max_value=1.0
            ),
        },
        use_container_width=True,
        hide_index=True
    )

finally:
    db.close()
