import io
import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from src.db import SessionLocal
from src.models import User, Project
from src.services.projects import list_projects_for_user
from src.services.risk import get_latest_risk_for_project
from dashboard.components import apply_custom_styles

st.set_page_config(page_title="Export Reports | Risk Agent", page_icon="📄", layout="wide")
apply_custom_styles()

if not st.session_state.get("authenticated", False):
    st.warning("Please sign in from the Login page first.")
    st.stop()

db = SessionLocal()
try:
    current_user = db.query(User).filter(User.id == st.session_state["user_id"]).first()
    projects = list_projects_for_user(db, current_user)

    st.title("📄 Export Risk & Progress Reports")
    st.markdown("Generate and export institutional risk assessment summaries as CSV or printable PDF documents.")

    if not projects:
        st.info("No projects available to export.")
        st.stop()

    rows = []
    for p in projects:
        r = get_latest_risk_for_project(db, p.id)
        bucket = r.bucket if r else "Unscored"
        prob = f"{r.probability:.1%}" if r else "N/A"
        factor_desc = r.top_factors[0].get("description", "-") if (r and r.top_factors) else "-"

        rows.append({
            "Project ID": p.id,
            "Project Title": p.title,
            "Type": p.type,
            "Semester": p.semester,
            "Guide": p.guide.user.name if p.guide and p.guide.user else "Unassigned",
            "Risk Bucket": bucket,
            "Delay Probability": prob,
            "Primary Driver": factor_desc
        })

    df = pd.DataFrame(rows)
    st.subheader("Report Preview")
    st.dataframe(df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)

    # 1. CSV Download
    with c1:
        csv_data = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Export as CSV Spreadsheet",
            data=csv_data,
            file_name="project_risk_report.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 2. PDF Download using ReportLab
    with c2:
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1e293b")
        )
        elements.append(Paragraph("Student Project Progress & Delay Risk Report", title_style))
        elements.append(Paragraph(f"Generated for: {current_user.name} ({current_user.role.title()})", styles["Normal"]))
        elements.append(Spacer(1, 16))

        # Table data for PDF
        table_data = [["ID", "Title", "Sem", "Guide", "Risk", "Prob", "Primary Driver"]]
        for r in rows:
            table_data.append([
                str(r["Project ID"]),
                r["Project Title"][:24] + "..." if len(r["Project Title"]) > 24 else r["Project Title"],
                r["Semester"],
                r["Guide"][:16],
                r["Risk Bucket"],
                r["Delay Probability"],
                r["Primary Driver"][:30] + "..." if len(r["Primary Driver"]) > 30 else r["Primary Driver"]
            ])

        pdf_table = Table(table_data, colWidths=[25, 130, 60, 85, 45, 45, 150])
        pdf_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ]))
        elements.append(pdf_table)

        doc.build(elements)
        pdf_data = pdf_buffer.getvalue()

        st.download_button(
            label="⬇️ Export as PDF Document",
            data=pdf_data,
            file_name="project_risk_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

finally:
    db.close()
