import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date
from src.db import SessionLocal
from src.models import User, Project, Milestone, Review, ActionItem, ProgressLog, RiskScore
from src.services.projects import list_projects_for_user, get_project_by_id
from src.services.reviews import add_review, update_action_item_status
from src.services.progress import add_progress_log
from src.services.risk import score_and_record_project_risk, get_risk_history_for_project
from dashboard.components import apply_custom_styles, render_risk_badge, render_empty_state

st.set_page_config(page_title="Project Details | Risk Agent", page_icon="📁", layout="wide")
apply_custom_styles()

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the Login page first.")
    st.stop()

db = SessionLocal()
try:
    current_user = db.query(User).filter(User.id == st.session_state["user_id"]).first()
    projects = list_projects_for_user(db, current_user)

    if not projects:
        render_empty_state(title="No Projects Available", description="No projects are currently accessible for your account.")
        st.stop()

    proj_options = {f"#{p.id} - {p.title} ({p.semester})": p.id for p in projects}
    selected_label = st.selectbox("Select Project to Inspect", list(proj_options.keys()))
    project_id = proj_options[selected_label]
    project = get_project_by_id(db, project_id, current_user)

    st.title(f"📁 {project.title}")
    
    # Header summary
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"**Type:** `{project.type}`")
        st.markdown(f"**Semester:** `{project.semester}`")
    with c2:
        st.markdown(f"**Guide:** {project.guide.user.name if project.guide and project.guide.user else 'None'}")
        st.markdown(f"**Team Size:** {project.team_size} members")
    with c3:
        st.markdown(f"**Start Date:** `{project.start_date}`")
        st.markdown(f"**Planned End:** `{project.planned_end_date}`")
    with c4:
        st.markdown(f"**Status:** `{project.status.upper()}`")
        if st.button("🔄 Recalculate Risk Now", key="recalc_risk"):
            score_rec = score_and_record_project_risk(db, project, creator_id=current_user.id)
            st.success(f"Updated risk: {score_rec.bucket} ({score_rec.probability:.1%}) [{score_rec.model_version}]")
            st.rerun()

    st.markdown("---")

    # Tabs for comprehensive inspection
    tab_risk, tab_milestones, tab_reviews, tab_progress = st.tabs([
        "🤖 Risk & SHAP Factors",
        "🎯 Milestones & Burndown",
        "📝 Reviews & Action Items",
        "📈 Weekly Progress Logs"
    ])

    with tab_risk:
        col_r1, col_r2 = st.columns([1, 1.3])
        history = get_risk_history_for_project(db, project.id)

        with col_r1:
            st.subheader("Current Risk Assessment")
            if history:
                latest = history[-1]
                st.markdown(f"#### Status: {render_risk_badge(latest.bucket)}", unsafe_allow_html=True)
                st.metric("Predicted Delay Probability", f"{latest.probability:.1%}")
                st.markdown(f"**Active Scorer:** `{latest.model_version}`")
                
                st.markdown("##### 🔍 Top Delay Drivers")
                for f in latest.top_factors:
                    desc = f.get("description", str(f))
                    imp = f.get("impact", 0.0)
                    st.markdown(f"- **{desc}** *(Impact: +{imp:.2f})*")
            else:
                st.info("No risk score calculated yet. Click 'Recalculate Risk Now' above.")

        with col_r2:
            st.subheader("Historical Risk Trajectory")
            if len(history) > 1:
                hist_df = pd.DataFrame([{
                    "Date": h.as_of_date,
                    "Probability": h.probability,
                    "Bucket": h.bucket
                } for h in history])
                fig = px.line(hist_df, x="Date", y="Probability", markers=True, title="Risk Trend Over Time")
                fig.update_layout(yaxis_range=[0, 1])
                st.plotly_chart(fig, use_container_width=True)
            elif history:
                st.info("Only 1 risk assessment on record. Trend chart will display as more assessments occur.")
            else:
                st.info("No history available.")

    with tab_milestones:
        st.subheader("Milestones & Planned vs Actual")
        milestones = db.query(Milestone).filter(Milestone.project_id == project.id).order_by(Milestone.planned_date.asc()).all()
        if milestones:
            ms_data = [{
                "Milestone": m.name,
                "Planned Date": m.planned_date,
                "Planned Cumulative %": f"{m.planned_pct:.1f}%",
                "Completed Date": m.completed_date or "Pending"
            } for m in milestones]
            st.dataframe(pd.DataFrame(ms_data), use_container_width=True, hide_index=True)
        else:
            st.info("No milestones specified for this project.")

    with tab_reviews:
        st.subheader("Review History & Action Items")
        reviews = db.query(Review).filter(Review.project_id == project.id).order_by(Review.review_date.desc()).all()
        
        # Add Review Form (Guides and Admin)
        if current_user.role in ["guide", "admin"]:
            with st.expander("➕ Conduct New Project Review"):
                with st.form("new_review_form"):
                    r_date = st.date_input("Review Date", date.today())
                    score = st.slider("Evaluation Score (out of 20)", 0.0, 20.0, 15.0, 0.5)
                    att = st.slider("Team Attendance", 0.0, 1.0, 1.0, 0.1)
                    comment = st.text_area("Reviewer Observations & Feedback", placeholder="Describe technical blockers, sprint velocity, or milestones reached...")
                    action_item_desc = st.text_input("New Action Item Description", placeholder="e.g. Complete module 2 tests, fix API response schema")
                    action_due = st.date_input("Action Item Due Date", date.today() + pd.Timedelta(days=14))
                    
                    submit_rev = st.form_submit_button("Record Review")
                    if submit_rev:
                        items = []
                        if action_item_desc:
                            items.append({"description": action_item_desc, "due_date": action_due, "status": "pending"})
                        add_review(
                            db=db,
                            project_id=project.id,
                            review_date=r_date,
                            rubric_scores={"total": score},
                            attendance=att,
                            reviewer_comment=comment,
                            action_items_list=items,
                            creator_id=current_user.id
                        )
                        # Re-score immediately
                        score_and_record_project_risk(db, project, creator_id=current_user.id)
                        st.success("Review and action item successfully recorded!")
                        st.rerun()

        # Display Existing Reviews
        if reviews:
            for rev in reviews:
                st.markdown(f"""
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between;">
                        <b>Review Date: {rev.review_date}</b>
                        <span style="color: #6366f1; font-weight: 600;">Score: {rev.rubric_scores.get('total', 'N/A')}/20</span>
                    </div>
                    <p style="margin-top: 8px; color: #cbd5e1;"><i>"{rev.reviewer_comment}"</i></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No reviews recorded yet.")

        # Action Items Section
        st.subheader("Outstanding & Completed Action Items")
        action_items = db.query(ActionItem).filter(ActionItem.project_id == project.id).all()
        if action_items:
            for ai in action_items:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"**Task:** {ai.description} *(Due: {ai.due_date})*")
                with col_b:
                    new_st = st.selectbox(
                        "Status",
                        ["pending", "completed", "overdue"],
                        index=["pending", "completed", "overdue"].index(ai.status),
                        key=f"ai_status_{ai.id}"
                    )
                    if new_st != ai.status:
                        update_action_item_status(db, ai.id, new_st, user_id=current_user.id)
                        st.success("Status updated!")
                        st.rerun()
        else:
            st.info("No action items assigned.")

    with tab_progress:
        st.subheader("Weekly Progress Submissions")

        # Submit Progress Form (Students, Guides, Admin)
        with st.expander("➕ Submit Weekly Progress Update"):
            with st.form("new_progress_form"):
                w_start = st.date_input("Week Starting Date", date.today())
                pct = st.number_input("Milestone Completion Percentage (0-100%)", 0.0, 100.0, 25.0, 1.0)
                commits = st.number_input("Commits / Document Updates", 0, 100, 5)
                missed = st.number_input("Missed Meetings", 0, 10, 0)
                slips = st.number_input("Deadline Slips", 0, 10, 0)
                notes = st.text_area("Weekly Summary & Challenges Faced")
                submit_prog = st.form_submit_button("Submit Progress Log")
                if submit_prog:
                    add_progress_log(
                        db=db,
                        project_id=project.id,
                        week_start=w_start,
                        milestone_completion_pct=pct,
                        commits_or_updates=commits,
                        missed_meetings=missed,
                        deadline_slips=slips,
                        notes=notes,
                        creator_id=current_user.id
                    )
                    score_and_record_project_risk(db, project, creator_id=current_user.id)
                    st.success("Progress log recorded and project re-scored!")
                    st.rerun()

        # History of logs
        logs = db.query(ProgressLog).filter(ProgressLog.project_id == project.id).order_by(ProgressLog.week_start.asc()).all()
        if logs:
            log_data = [{
                "Week Start": l.week_start,
                "Completion %": f"{l.milestone_completion_pct:.1f}%",
                "Commits/Updates": l.commits_or_updates,
                "Missed Meetings": l.missed_meetings,
                "Slips": l.deadline_slips,
                "Notes": l.notes
            } for l in logs]
            st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
            
            # Progress Line Chart
            cdf = pd.DataFrame([{
                "Week": l.week_start,
                "Completion %": l.milestone_completion_pct
            } for l in logs])
            fig_p = px.line(cdf, x="Week", y="Completion %", title="Actual Milestone Completion Velocity", markers=True)
            fig_p.update_layout(yaxis_range=[0, 100])
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            st.info("No weekly progress logs recorded.")

finally:
    db.close()
