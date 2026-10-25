import streamlit as st
import pandas as pd
from src.db import SessionLocal
from src.models import User
from src.importers import (
    import_projects_dataframe,
    import_reviews_dataframe,
    import_progress_dataframe,
    generate_csv_template
)
from dashboard.components import apply_custom_styles, render_empty_state

st.set_page_config(page_title="Data Import | Risk Agent", page_icon="📥", layout="wide")
apply_custom_styles()

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the Login page first.")
    st.stop()

db = SessionLocal()
try:
    current_user = db.query(User).filter(User.id == st.session_state["user_id"]).first()
    if current_user.role not in ["admin", "guide"]:
        st.error("Only Administrators and Faculty Guides have permission to import bulk data.")
        st.stop()

    st.title("📥 Bulk Data Import & Migration")
    st.markdown("Import projects, reviews, or progress logs from CSV or Excel files with dynamic column mapping and real-time validation.")

    import_type = st.radio(
        "Select Entity Type to Import",
        ["Projects", "Reviews", "Weekly Progress Logs"],
        horizontal=True
    )

    # Download Sample Template
    type_key = "projects" if import_type == "Projects" else ("reviews" if import_type == "Reviews" else "progress")
    csv_template = generate_csv_template(type_key)
    st.download_button(
        label=f"⬇️ Download Sample {import_type} CSV Template",
        data=csv_template,
        file_name=f"{type_key}_sample_template.csv",
        mime="text/csv"
    )

    st.markdown("---")

    uploaded_file = st.file_uploader(f"Upload {import_type} File (CSV or Excel)", type=["csv", "xlsx", "xls"])

    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

        st.subheader("📋 File Preview (Top 5 Rows)")
        st.dataframe(df.head(5), use_container_width=True)

        cols = list(df.columns)
        st.subheader("🔀 Step 2: Map Columns to System Fields")

        mapping = {}
        if import_type == "Projects":
            standard_fields = {
                "title": ("Project Title *", 0),
                "semester": ("Semester", min(1, len(cols)-1)),
                "planned_end_date": ("Planned End Date *", min(2, len(cols)-1)),
                "start_date": ("Start Date", min(3, len(cols)-1)),
                "type": ("Project Type", min(4, len(cols)-1)),
                "team_size": ("Team Size", min(5, len(cols)-1)),
                "guide_email": ("Faculty Guide Email", min(6, len(cols)-1))
            }
        elif import_type == "Reviews":
            standard_fields = {
                "project_id": ("Project ID *", 0),
                "review_date": ("Review Date", min(1, len(cols)-1)),
                "score": ("Review Score (0-20)", min(2, len(cols)-1)),
                "comment": ("Reviewer Observations / Comment", min(3, len(cols)-1))
            }
        else:
            standard_fields = {
                "project_id": ("Project ID *", 0),
                "week_start": ("Week Starting Date", min(1, len(cols)-1)),
                "completion_pct": ("Milestone Completion %", min(2, len(cols)-1)),
                "commits_or_updates": ("Commits / Updates Count", min(3, len(cols)-1)),
                "deadline_slips": ("Deadline Slips Count", min(4, len(cols)-1)),
                "missed_meetings": ("Missed Meetings Count", min(5, len(cols)-1))
            }

        col_left, col_right = st.columns(2)
        half = len(standard_fields) // 2 + 1
        for idx, (field_key, (field_label, default_idx)) in enumerate(standard_fields.items()):
            target_col = col_left if idx < half else col_right
            with target_col:
                selected_col = st.selectbox(
                    f"Match: {field_label}",
                    cols,
                    index=default_idx,
                    key=f"map_{field_key}"
                )
                mapping[selected_col] = field_key

        st.markdown("---")
        if st.button("🚀 Process & Import Data", type="primary", use_container_width=True):
            with st.spinner("Validating rows and committing to database..."):
                if import_type == "Projects":
                    success, errors = import_projects_dataframe(db, df, mapping, creator_id=current_user.id)
                elif import_type == "Reviews":
                    success, errors = import_reviews_dataframe(db, df, mapping, creator_id=current_user.id)
                else:
                    success, errors = import_progress_dataframe(db, df, mapping, creator_id=current_user.id)

            st.success(f"Successfully imported {success} record(s)!")
            if errors:
                st.warning(f"⚠️ {len(errors)} row(s) failed validation. Check details below:")
                err_df = pd.DataFrame(errors)
                st.dataframe(err_df, use_container_width=True)

                # Download error report
                err_csv = err_df.to_csv(index=False)
                st.download_button(
                    "⬇️ Download Error Report (CSV)",
                    err_csv,
                    file_name="import_error_report.csv",
                    mime="text/csv"
                )

finally:
    db.close()
