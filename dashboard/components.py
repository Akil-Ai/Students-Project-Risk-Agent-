import streamlit as st

def apply_custom_styles():
    """Applies modern clean CSS styling with dark/light harmony, glassmorphism cards, and badge accents."""
    st.markdown("""
        <style>
        /* Main background and clean typography */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        /* Metric card styling */
        .metric-card {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 18px 22px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            border-color: rgba(99, 102, 241, 0.4);
        }
        .metric-label {
            font-size: 0.82rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }
        .metric-value {
            font-size: 1.85rem;
            font-weight: 700;
            color: #f8fafc;
        }

        /* Risk Badges */
        .badge-risk-high {
            background-color: rgba(239, 68, 68, 0.15);
            color: #f87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-risk-medium {
            background-color: rgba(245, 158, 11, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.3);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
        }
        .badge-risk-low {
            background-color: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 0.78rem;
            font-weight: 600;
            display: inline-block;
        }

        /* Alert Pill */
        .alert-pill {
            background: rgba(30, 41, 59, 0.7);
            border-left: 4px solid #ef4444;
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 12px;
        }
        </style>
    """, unsafe_allow_html=True)

def render_metric_card(label: str, value: str, subtext: str = ""):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {f'<div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">{subtext}</div>' if subtext else ''}
        </div>
    """, unsafe_allow_html=True)

def render_risk_badge(bucket: str) -> str:
    if bucket == "High":
        return f'<span class="badge-risk-high">● High Risk</span>'
    elif bucket == "Medium":
        return f'<span class="badge-risk-medium">● Medium Risk</span>'
    else:
        return f'<span class="badge-risk-low">● Low Risk</span>'

def render_empty_state(title: str, description: str, action_label: str = None):
    st.markdown(f"""
        <div style="text-align: center; padding: 45px 20px; border: 2px dashed rgba(255, 255, 255, 0.15); border-radius: 14px; margin: 25px 0;">
            <div style="font-size: 2.2rem; margin-bottom: 10px;">📋</div>
            <h3 style="color: #cbd5e1; margin-bottom: 6px;">{title}</h3>
            <p style="color: #64748b; font-size: 0.92rem; max-width: 450px; margin: 0 auto 16px auto;">{description}</p>
        </div>
    """, unsafe_allow_html=True)
