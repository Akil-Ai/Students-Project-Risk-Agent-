import streamlit as st
import json
import pandas as pd
from src.db import SessionLocal
from src.models import User, Guide, Student, Setting
from src.services.auth import create_user
from src.services.settings import get_all_settings, update_setting
from src.scheduler import scheduler
from dashboard.components import apply_custom_styles, render_metric_card

st.set_page_config(page_title="Admin Panel | Risk Agent", page_icon="⚙️", layout="wide")
apply_custom_styles()

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the Login page first.")
    st.stop()

db = SessionLocal()
try:
    current_user = db.query(User).filter(User.id == st.session_state["user_id"]).first()
    if current_user.role != "admin":
        st.error("Admin page access is strictly restricted to Administrators.")
        st.stop()

    st.title("⚙️ System Administration & Configuration")
    st.markdown("User provisioning, live runtime setting updates, and scheduler heartbeat.")

    tab_users, tab_settings, tab_scheduler = st.tabs([
        "👥 User Management",
        "🎛️ Runtime Settings Editor",
        "⏱️ Scheduler Status"
    ])

    with tab_users:
        st.subheader("Add New System User")
        with st.form("create_user_form"):
            cu_name = st.text_input("Full Name", placeholder="e.g. Dr. Jane Doe")
            cu_email = st.text_input("Institutional Email", placeholder="e.g. jdoe@college.edu")
            cu_pass = st.text_input("Password", type="password")
            cu_role = st.selectbox("Role", ["guide", "student", "admin"])
            cu_dept = st.text_input("Department (for Guides)", value="Computer Science")
            cu_usn = st.text_input("USN / Roll Number (for Students)", placeholder="e.g. 1MS22CS045")
            
            submit_user = st.form_submit_button("Create User Account")
            if submit_user:
                if not cu_name or not cu_email or not cu_pass:
                    st.error("Please fill in Name, Email, and Password.")
                else:
                    try:
                        new_u = create_user(
                            db=db,
                            name=cu_name,
                            email=cu_email,
                            password=cu_pass,
                            role=cu_role,
                            department=cu_dept,
                            usn_or_roll=cu_usn,
                            creator_id=current_user.id
                        )
                        st.success(f"Successfully created user {new_u.email} ({new_u.role})!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error creating user: {e}")

        st.subheader("Existing System Users")
        users = db.query(User).all()
        user_rows = [{
            "ID": u.id,
            "Name": u.name,
            "Email": u.email,
            "Role": u.role.upper(),
            "Created": u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "-"
        } for u in users]
        st.dataframe(pd.DataFrame(user_rows), use_container_width=True, hide_index=True)

    with tab_settings:
        st.subheader("Runtime Settings Editor")
        st.caption("Settings modified here take effect immediately in application logic without restart.")

        settings = get_all_settings(db)
        for key, s_data in settings.items():
            with st.expander(f"🔧 {key}"):
                st.caption(f"**Description:** {s_data['description']}")
                curr_val = s_data['value']
                
                # Check if JSON
                is_json = False
                try:
                    if curr_val.startswith("{") or curr_val.startswith("["):
                        is_json = True
                except Exception:
                    pass

                if is_json:
                    new_val = st.text_area(f"Value for {key}", value=curr_val, height=120, key=f"input_{key}")
                else:
                    new_val = st.text_input(f"Value for {key}", value=curr_val, key=f"input_{key}")

                if st.button("Save Setting", key=f"save_{key}"):
                    try:
                        update_setting(db, key, new_val)
                        st.success(f"Updated '{key}' successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating setting: {e}")

    with tab_scheduler:
        st.subheader("APScheduler Heartbeat & Background Jobs")
        is_running = scheduler.running
        status_text = "🟢 ACTIVE & RUNNING" if is_running else "🔴 STOPPED"
        render_metric_card("Scheduler Engine", status_text, "Executes periodic risk scoring and alert generation")

        jobs = scheduler.get_jobs()
        if jobs:
            st.markdown("##### Registered Jobs:")
            for j in jobs:
                st.markdown(f"- **Job ID:** `{j.id}` | **Next Run:** `{j.next_run_time}`")
        else:
            st.info("No active jobs scheduled.")

finally:
    db.close()
