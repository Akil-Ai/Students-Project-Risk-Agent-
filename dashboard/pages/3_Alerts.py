import streamlit as st
import pandas as pd
from src.db import SessionLocal
from src.models import User, Alert, Project
from src.services.projects import list_projects_for_user
from src.services.alerts import record_alert_feedback
from dashboard.components import apply_custom_styles, render_empty_state, render_metric_card

st.set_page_config(page_title="Alerts Inbox | Risk Agent", page_icon="🚨", layout="wide")
apply_custom_styles()

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the Login page first.")
    st.stop()

db = SessionLocal()
try:
    current_user = db.query(User).filter(User.id == st.session_state["user_id"]).first()
    user_projects = list_projects_for_user(db, current_user)
    proj_ids = [p.id for p in user_projects]

    st.title("🚨 Alerts & Early Interventions")
    st.markdown("Intelligent risk notifications, jump warnings, and guide feedback.")

    if not proj_ids:
        render_empty_state(title="No Alerts Found", description="You have no assigned projects or alerts to review.")
        st.stop()

    # Filter alerts for current user's accessible projects
    alerts_query = db.query(Alert).filter(Alert.project_id.in_(proj_ids))

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        status_filter = st.selectbox("Status Filter", ["All", "Open Only", "Resolved / Dismissed"])
    with col_f2:
        type_filter = st.selectbox("Alert Type", ["All", "HIGH_RISK", "RISK_JUMP"])

    if status_filter == "Open Only":
        alerts_query = alerts_query.filter(Alert.status == "open")
    elif status_filter == "Resolved / Dismissed":
        alerts_query = alerts_query.filter(Alert.status.in_(["resolved", "dismissed"]))

    if type_filter != "All":
        alerts_query = alerts_query.filter(Alert.type == type_filter)

    alerts = alerts_query.order_by(Alert.created_at.desc()).all()

    # Metrics
    open_count = db.query(Alert).filter(Alert.project_id.in_(proj_ids), Alert.status == "open").count()
    total_count = db.query(Alert).filter(Alert.project_id.in_(proj_ids)).count()

    m1, m2 = st.columns(2)
    with m1:
        render_metric_card("Active Open Alerts", str(open_count), "Requiring guide attention or feedback")
    with m2:
        render_metric_card("Total Lifetime Alerts", str(total_count), "Logged across all project milestones")

    st.markdown("---")

    if not alerts:
        render_empty_state(
            title="Inbox Clean",
            description="No alerts currently match your filter criteria. All monitored projects are on track!"
        )
    else:
        for alert in alerts:
            proj = alert.project
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-left: 5px solid {'#ef4444' if alert.type == 'HIGH_RISK' else '#f59e0b'}; border-radius: 10px; padding: 18px 24px; margin-bottom: 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 1.15rem; font-weight: 700; color: #f8fafc;">#{proj.id} - {proj.title}</span>
                    <span style="background: rgba(255, 255, 255, 0.1); padding: 4px 10px; border-radius: 6px; font-size: 0.82rem; color: #cbd5e1;">{alert.type} • {alert.created_at.strftime('%Y-%m-%d %H:%M')}</span>
                </div>
                <div style="color: #cbd5e1; font-size: 0.95rem; margin-bottom: 8px;">
                    <b>Trigger Reasons:</b>
                    <ul style="margin: 4px 0 10px 20px;">
                        {''.join(f'<li>{r}</li>' for r in alert.reasons)}
                    </ul>
                </div>
                <div style="background: rgba(99, 102, 241, 0.1); border: 1px dashed rgba(99, 102, 241, 0.4); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;">
                    <span style="color: #a5b4fc; font-weight: 600;">💡 Recommended Guide Action:</span>
                    <span style="color: #e0e7ff;"> {alert.suggested_action}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_act1, col_act2, col_act3 = st.columns([1, 1, 2])
            with col_act1:
                if st.button("👍 Useful Alert", key=f"useful_{alert.id}"):
                    record_alert_feedback(db, alert.id, feedback="useful", user_id=current_user.id)
                    st.success("Feedback recorded: Useful")
                    st.rerun()
            with col_act2:
                if st.button("👎 Not Useful", key=f"not_useful_{alert.id}"):
                    record_alert_feedback(db, alert.id, feedback="not_useful", user_id=current_user.id)
                    st.info("Feedback recorded: Not Useful")
                    st.rerun()
            with col_act3:
                if alert.status == "open":
                    if st.button("✅ Mark as Resolved", key=f"resolve_{alert.id}"):
                        record_alert_feedback(db, alert.id, feedback=alert.feedback, new_status="resolved", user_id=current_user.id)
                        st.success("Alert resolved!")
                        st.rerun()
                else:
                    st.markdown(f"Status: **{alert.status.upper()}** (Feedback: `{alert.feedback}`)")

finally:
    db.close()
