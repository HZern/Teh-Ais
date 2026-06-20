import streamlit as st
import requests
from datetime import datetime
import html

# ==========================================================
# Security Manager Page
# Manager-level security findings dashboard
# Secure & Energy-Aware Cloud Platform for Construction Tech
# ==========================================================

st.set_page_config(
    page_title="CloudOps Security Manager",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

PRIORITY_ORDER = {
    "Danger": 1,
    "Warning": 2,
    "Low": 3
}

STATUS_COLORS = {
    "Open": "🔴",
    "In Progress": "🟠",
    "Resolved": "🟢",
    "Flagged": "🔴",
}

API_URL = "http://127.0.0.1:8000/alerts"


def streamlit_fragment(*args, **kwargs):
    if hasattr(st, "fragment"):
        return st.fragment(*args, **kwargs)

    def decorator(function):
        return function

    return decorator


# Cache only for 10 seconds, matching the refresh interval.
# If you want every refresh to call backend directly, remove this decorator.
@st.cache_data(ttl=10)
def fetch_security_alerts():
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        return {
            "alerts": data.get("alerts", []),
            "count": data.get("count", 0),
            "message": data.get("message", "Scanner returned alerts"),
            "error": None,
            "last_updated": datetime.now().strftime("%I:%M:%S %p")
        }

    except requests.exceptions.RequestException as error:
        return {
            "alerts": [],
            "count": 0,
            "message": "Failed to connect to backend",
            "error": str(error),
            "last_updated": datetime.now().strftime("%I:%M:%S %p")
        }


# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f7fafc !important;
        color: #0f172a !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #f7fafc !important;
        color: #0f172a !important;
    }

    [data-testid="stHeader"] {
        background-color: #f7fafc !important;
    }

    [data-testid="stToolbar"] {
        background-color: #f7fafc !important;
    }

    [data-testid="stSidebar"] {
        background-color: #f1f5f9 !important;
    }

    [data-testid="stSidebar"] * {
        color: #0f172a !important;
    }

    div[data-testid="stVerticalBlock"] {
        color: #0f172a !important;
    }

    p, span, div, label {
        color: inherit;
    }
    
    div[data-testid="stButton"] > button[kind="secondary"] {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
    }

    div[data-testid="stButton"] > button[kind="secondary"]:hover {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
    }

    [data-testid="stSidebar"] div[data-testid="stButton"] > button p,
    [data-testid="stSidebar"] div[data-testid="stButton"] > button span {
        color: #ffffff !important;
        font-weight: 700 !important;
    }


    .main {
        background-color: #f7fafc;
    }

    [data-testid="stSidebarNav"] {
        display: none;
    }

.block-container {
    padding-top: 3rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

.hero-card {
    padding: 26px;
    border-radius: 18px;
    background: linear-gradient(135deg, #0f172a 0%, #0e7490 100%);
    color: white;
    margin-bottom: 28px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.18);
}

.hero-title {
    color: white !important;
    font-size: 34px;
    font-weight: 850;
    margin-bottom: 8px;
}

.hero-subtitle {
    color: white !important;
    font-size: 16px;
    opacity: 0.95;
    line-height: 1.5;
}

.section-heading {
    color: #0f172a !important;
    font-size: 32px;
    font-weight: 850;
    margin-top: 10px;
    margin-bottom: 8px;
}

.section-caption {
    color: #475569 !important;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 22px;
}

label,
[data-testid="stWidgetLabel"] p {
    color: #0f172a !important;
    font-weight: 750 !important;
}

div[data-baseweb="select"] > div {
    border-radius: 12px !important;
    background-color: #111827 !important;
    border: 1px solid #334155 !important;
    color: #ffffff !important;
    font-weight: 700 !important;
}

div[data-baseweb="select"] span {
    color: #ffffff !important;
    font-weight: 700 !important;
}

div[data-baseweb="select"] svg {
    fill: #ffffff !important;
}

div[data-testid="stSegmentedControl"] button {
    border-radius: 12px !important;
    font-weight: 750 !important;
}

div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
    background-color: #111827 !important;
    color: #ffffff !important;
}

.security-card {
    background: #ffffff;
    border: 1.5px solid #dbe3ee;
    border-radius: 18px;
    padding: 22px;
    margin-top: 18px;
    margin-bottom: 18px;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
}

.security-card:hover {
    border-color: #38bdf8;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
}

.security-topline {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 18px;
}

.security-title {
    color: #0f172a !important;
    font-size: 21px;
    font-weight: 850;
    margin-bottom: 8px;
}

.security-situation {
    color: #475569 !important;
    font-size: 15px;
    line-height: 1.5;
    margin-bottom: 14px;
}

.pill {
    display: inline-block;
    padding: 6px 11px;
    border-radius: 999px;
    background: #e0f2fe;
    color: #075985 !important;
    font-size: 13px;
    font-weight: 750;
    margin-right: 7px;
    margin-bottom: 8px;
}

.priority-danger {
    background: #fee2e2;
    color: #991b1b !important;
}

.priority-warning {
    background: #fef3c7;
    color: #92400e !important;
}

.priority-low {
    background: #dcfce7;
    color: #166534 !important;
}

.risk-level-box {
    min-width: 104px;
    text-align: center;
    padding: 12px 14px;
    border-radius: 14px;
    font-weight: 850;
    font-size: 16px;
    margin: 8px 12px 8px 0;
}

.risk-level-label {
    display: block;
    font-size: 11px;
    font-weight: 650;
    margin-top: 3px;
}

.risk-level-danger {
    background: #fee2e2;
    color: #991b1b !important;
    border: 1px solid #fecaca;
}

.risk-level-warning {
    background: #fef3c7;
    color: #92400e !important;
    border: 1px solid #fde68a;
}

.recommendation-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 18px;
    margin-top: 18px;
}

.recommendation-title {
    color: #0f172a !important;
    font-size: 17px;
    font-weight: 850;
    margin-bottom: 7px;
}

.recommendation-text {
    color: #334155 !important;
    font-size: 15px;
    line-height: 1.55;
    margin-bottom: 15px;
}

.smart-recommendation-box {
    background: #dcfce7;
    border-left: 5px solid #22c55e;
    border-radius: 12px;
    padding: 15px;
    margin-top: 10px;
}

.smart-recommendation-box p {
    color: #14532d !important;
    font-size: 15px;
    line-height: 1.55;
    font-weight: 650;
    margin: 0;
}

.smart-recommendation-box ul {
    color: #14532d !important;
    margin-top: 0;
    margin-bottom: 0;
    padding-left: 24px;
}

.smart-recommendation-box li {
    color: #14532d !important;
    font-size: 15px;
    line-height: 1.55;
    font-weight: 650;
    margin-bottom: 8px;
}

.metric-card {
    background: #ffffff;
    padding: 20px;
    border-radius: 16px;
    border: 2px solid #cbd5e1;
    border-top: 5px solid #0e7490;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14);
    min-height: 120px;
    margin-bottom: 24px;
}

.metric-label {
    color: #334155 !important;
    font-size: 14px;
    font-weight: 750;
    margin-bottom: 10px;
}

.metric-number {
    color: #020617 !important;
    font-size: 36px;
    font-weight: 900;
    line-height: 1.1;
}
</style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Helper Functions
# -----------------------------
def priority_class(risk):
    if risk == "Danger":
        return "priority-danger"
    if risk == "Warning":
        return "priority-warning"
    return ""


def risk_level_class(risk):
    if risk == "Danger":
        return "risk-level-danger"
    if risk == "Warning":
        return "risk-level-warning"
    return ""


def sort_security_findings(findings, sort_option):
    risk_order = {
        "Danger": 1,
        "Warning": 2
    }

    if sort_option == "Risk: Danger first":
        return sorted(
            findings,
            key=lambda x: risk_order.get(x.get("finding_type", "Warning"), 99)
        )

    if sort_option == "Risk: Warning first":
        return sorted(
            findings,
            key=lambda x: risk_order.get(x.get("finding_type", "Warning"), 99),
            reverse=True
        )

    if sort_option == "AWS Area A-Z":
        return sorted(findings, key=lambda x: x.get("area", ""))

    return findings


def render_recommendation(value):
    """
    Accepts either:
    - string recommendation
    - list of recommendation steps

    Returns safe HTML.
    """
    if isinstance(value, list):
        list_items = "".join(f"<li>{html.escape(str(item))}</li>" for item in value)
        return f"<ul>{list_items}</ul>"

    return f"<p>{html.escape(str(value))}</p>"


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("🔐 CloudOps Security")
    st.caption("Manager View")

    st.divider()

    st.markdown("### Switch View")

    if st.button("Workload Manager", use_container_width=True):
        st.switch_page("pages/workload_analytics.py")

    if st.button("🔐 Cloud Configuration Check", use_container_width=True):
        st.switch_page("pages/security_check.py")

    st.divider()

    st.markdown("### View")
    st.info("You are currently viewing the **security-focused manager page**.")


# -----------------------------
# Main Page Header
# -----------------------------
st.markdown(
    """
<div class="hero-card">
<div class="hero-title">Security Manager View 🔐</div>
<div class="hero-subtitle">
Review security findings in business-friendly language and view recommendations directly inside each card.
</div>
</div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
<h2 class="section-heading">Priority Tasks & Issues</h2>
<div class="section-caption">
Security findings are shown with manager-level explanations and recommendations.
</div>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Initial fetch for filter options
# -----------------------------
backend_result = fetch_security_alerts()
alerts = backend_result["alerts"]

if backend_result["error"]:
    st.error("Backend is not connected. Please start the backend using `python3 security_backend.py`.")
    st.caption(backend_result["error"])


# -----------------------------
# Filters
# -----------------------------
filter_col1, filter_col2, filter_col3 = st.columns([1.2, 1.2, 1.6])

with filter_col1:
    selected_area = st.selectbox(
        "Filter by AWS area",
        ["All"] + sorted(list(set(alert.get("area", "Unknown") for alert in alerts))),
        key="security_area_filter"
    )

with filter_col2:
    selected_security_risk = st.selectbox(
        "Filter by risk",
        ["All", "Danger", "Warning"],
        key="security_risk_filter"
    )

with filter_col3:
    security_sort_option = st.selectbox(
        "Arrange tasks by",
        [
            "Risk: Danger first",
            "Risk: Warning first",
            "AWS Area A-Z"
        ],
        key="security_sort_filter"
    )


# -----------------------------
# Manager/Technician Toggle
# -----------------------------
if hasattr(st, "segmented_control"):
    selected_view = st.segmented_control(
        "View mode",
        ["Manager", "Technician"],
        default="Manager",
        key="security_view_mode"
    )
else:
    selected_view = st.radio(
        "View mode",
        ["Manager", "Technician"],
        horizontal=True,
        key="security_view_mode"
    )

is_technician_view = selected_view == "Technician"


# -----------------------------
# Auto-updating alert section only
# -----------------------------
@streamlit_fragment(run_every="10s")
def render_security_alert_section(
    selected_area,
    selected_security_risk,
    security_sort_option,
    is_technician_view
):
    backend_result = fetch_security_alerts()
    alerts = backend_result["alerts"]

    if backend_result["error"]:
        st.error("Backend is not connected. Please start the backend using `python3 security_backend.py`.")
        st.caption(backend_result["error"])

    st.markdown(
        f"""
<div class="section-caption">
Last updated: <b>{backend_result["last_updated"]}</b> | 
Backend message: {backend_result["message"]}
</div>
        """,
        unsafe_allow_html=True
    )

    filtered_findings = alerts

    if selected_area != "All":
        filtered_findings = [
            alert for alert in filtered_findings
            if alert.get("area") == selected_area
        ]

    if selected_security_risk != "All":
        filtered_findings = [
            alert for alert in filtered_findings
            if alert.get("finding_type") == selected_security_risk
        ]

    filtered_findings = sort_security_findings(filtered_findings, security_sort_option)

    total_alerts = len(alerts)
    warning_count = len([alert for alert in alerts if alert.get("finding_type") == "Warning"])
    danger_count = len([alert for alert in alerts if alert.get("finding_type") == "Danger"])

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.markdown(
            f"""
<div class="metric-card">
<div class="metric-label">Total Alerts</div>
<div class="metric-number">{total_alerts}</div>
</div>
            """,
            unsafe_allow_html=True
        )

    with summary_col2:
        st.markdown(
            f"""
<div class="metric-card">
<div class="metric-label">Warnings</div>
<div class="metric-number">{warning_count}</div>
</div>
            """,
            unsafe_allow_html=True
        )

    with summary_col3:
        st.markdown(
            f"""
<div class="metric-card">
<div class="metric-label">Dangers</div>
<div class="metric-number">{danger_count}</div>
</div>
            """,
            unsafe_allow_html=True
        )

    if not filtered_findings:
        st.warning("No security alerts match the current filters.")
        return

    for alert in filtered_findings:
        finding_type = alert.get("finding_type", "Warning")
        manager_view = alert.get("manager_view", {})
        technician_view = alert.get("technician_view", {})

        if is_technician_view:
            title = alert.get("resource_name", "Unknown resource")
            description = technician_view.get("technical_reason", "No technical reason provided.")
            risk_label = "Failed Rule"
            risk_text = technician_view.get("rule", "No failed rule provided.")
            aws_part_label = "AWS Resource Type"
            aws_part = alert.get("resource_type", "Unknown AWS resource")

            technical_fix = technician_view.get("technical_fix", "No technical recommendation provided.")
            recommendation = render_recommendation(technical_fix)

            resource_extra = technician_view.get("resource_id", "No resource ID provided.")
            resource_details_html = f"""
<div class="recommendation-title">Resource Details</div>
<div class="recommendation-text">{html.escape(str(resource_extra))}</div>
"""

            card_icon = "🛠️"
            card_label = "Technician View"

        else:
            title = manager_view.get("title", "Security alert")
            description = manager_view.get("situation", "No situation provided.")
            risk_label = "Risk"
            risk_text = manager_view.get("business_risk", "No business risk provided.")
            aws_part_label = "AWS Part to Fix"
            aws_part = manager_view.get("aws_part_to_fix", alert.get("area", "Unknown AWS area"))

            manager_recommendation = manager_view.get("recommended_action", "No recommendation provided.")
            recommendation = render_recommendation(manager_recommendation)

            resource_details_html = ""
            card_icon = "🔐"
            card_label = "Manager View"

        card_html = f"""
<div class="security-card">
<div class="security-topline">
<div>
<div class="security-title">{card_icon} {html.escape(str(title))}</div>
<div class="security-situation">{html.escape(str(description))}</div>
</div>
<div class="risk-level-box {risk_level_class(finding_type)}">
{html.escape(str(finding_type))}
<span class="risk-level-label">Risk Level</span>
</div>
</div>
<div class="recommendation-box">
<div class="recommendation-title">{risk_label}</div>
<div class="recommendation-text">{html.escape(str(risk_text))}</div>
<div class="recommendation-title">{aws_part_label}</div>
<div class="recommendation-text">{html.escape(str(aws_part))}</div>
{resource_details_html}
<div class="recommendation-title">Recommendation</div>
<div class="smart-recommendation-box">
{recommendation}
</div>
</div>
</div>
"""

        st.markdown(card_html, unsafe_allow_html=True)


render_security_alert_section(
    selected_area,
    selected_security_risk,
    security_sort_option,
    is_technician_view
)
