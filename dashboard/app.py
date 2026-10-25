import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st
from src.db import init_db, SessionLocal
from src.models import User
from src.services.auth import authenticate_user, bootstrap_admin_if_empty
from src.services.settings import sync_settings_from_config
from src.scheduler import start_scheduler
from dashboard.components import apply_custom_styles

st.set_page_config(
    page_title="Student Project Risk Agent",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global styles
apply_custom_styles()

# Initialize DB, base settings & start scheduler
init_db()
db = SessionLocal()
try:
    sync_settings_from_config(db)
    bootstrap_admin_if_empty(db)
    start_scheduler()
finally:
    db.close()

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["user_id"] = None
    st.session_state["user_name"] = None
    st.session_state["user_email"] = None
    st.session_state["user_role"] = None

def login_form():
    st.title("🎓 Student Project Review & Progress Risk Agent")
    st.markdown("Predictive early-warning system and intervention agent for college project teams.")

    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 14px; padding: 28px 32px; margin-top: 20px;">
                <h3 style="margin-top:0;">Sign In</h3>
                <p style="color: #94a3b8; font-size: 0.88rem;">Access role-based project dashboards and analytics.</p>
            </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            email = st.text_input("Institutional Email", placeholder="e.g., admin@college.edu, guide1@college.edu")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In to Portal", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    db = SessionLocal()
                    try:
                        user = authenticate_user(db, email, password)
                        if user:
                            st.session_state["authenticated"] = True
                            st.session_state["user_id"] = user.id
                            st.session_state["user_name"] = user.name
                            st.session_state["user_email"] = user.email
                            st.session_state["user_role"] = user.role
                            st.success(f"Welcome, {user.name} ({user.role.title()})!")
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
                    finally:
                        db.close()

        st.info("💡 **Default Credentials:**\n- **Admin:** `admin@college.edu` / `Admin@123456`\n- **Guide:** `guide1@college.edu` / `Password@123` (after demo seed)\n- **Student:** `student1@college.edu` / `Password@123` (after demo seed)")

if not st.session_state["authenticated"]:
    login_form()
else:
    # Sidebar user card and logout
    st.sidebar.markdown(f"### 👤 {st.session_state['user_name']}")
    st.sidebar.markdown(f"**Role:** `{st.session_state['user_role'].upper()}`")
    st.sidebar.markdown(f"**Email:** {st.session_state['user_email']}")
    
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.session_state["user_id"] = None
        st.session_state["user_name"] = None
        st.session_state["user_email"] = None
        st.session_state["user_role"] = None
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.info("💡 Use the pages above to navigate through Overview, Projects, Alerts, Model, and Admin settings.")

    # Main welcome view
    st.title("🎓 Project Risk Agent Dashboard")
    st.markdown(f"Welcome back, **{st.session_state['user_name']}**! Select an action or view from the navigation menu on the left.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        #### 📊 Overview & Risk Scores
        Real-time monitoring of project delay probabilities, progress gaps, and dynamic risk badges.
        """)
    with c2:
        st.markdown("""
        #### 🚨 Early Warning Alerts
        Intelligent alerts triggered by risk jumps or severe milestone slips with actionable guidance.
        """)
    with c3:
        st.markdown("""
        #### 🤖 Explainable ML Pipeline
        LightGBM & SHAP explainability showing top drivers behind every student delay prediction.
        """)
