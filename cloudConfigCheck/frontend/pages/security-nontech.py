import streamlit as st
from datetime import datetime

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

# -----------------------------
# Dummy Security Data
# Replace later with backend/API/security scan data
# -----------------------------
SECURITY_FINDINGS = [
    {
        "id": 1,
        "risk": "Danger",
        "status": "Open",
        "finding_type": "Public Storage",
        "resource_name": "bim-project-files-bucket",
        "manager_view": {
            "title": "Public Storage alert for bim-project-files-bucket",
            "situation": "A storage bucket containing BIM and construction project files is publicly accessible.",
            "business_risk": "Sensitive project documents may be exposed to unauthorized users, increasing the risk of data leakage, contractual issues, and client trust loss.",
            "recommended_action": "Restrict public access immediately and allow access only to approved project team members."
        }
    },
    {
        "id": 2,
        "risk": "Danger",
        "status": "Open",
        "finding_type": "CVE",
        "resource_name": "construction-db-prod",
        "manager_view": {
            "title": "CVE alert for construction-db-prod",
            "situation": "The production database is running a version affected by a known security vulnerability.",
            "business_risk": "Operational data could be compromised if the vulnerability is exploited, potentially disrupting construction workflows and exposing project information.",
            "recommended_action": "Ask the engineering team to schedule an urgent patch window and confirm that a backup exists before patching."
        }
    },
    {
        "id": 3,
        "risk": "Warning",
        "status": "In Progress",
        "finding_type": "Misconfiguration",
        "resource_name": "site-monitoring-api",
        "manager_view": {
            "title": "Misconfiguration alert for site-monitoring-api",
            "situation": "The API service allows broader network access than required.",
            "business_risk": "Attackers may have more opportunities to access internal construction workflow systems or site monitoring data.",
            "recommended_action": "Limit access to approved networks and request a firewall rule review from the engineering team."
        }
    },
    {
        "id": 4,
        "risk": "Warning",
        "status": "Open",
        "finding_type": "Identity Access",
        "resource_name": "project-admin-role",
        "manager_view": {
            "title": "Identity Access alert for project-admin-role",
            "situation": "An admin role has more permissions than required for daily project operations.",
            "business_risk": "Excessive permissions increase the impact of accidental misuse or compromised accounts.",
            "recommended_action": "Review the role and apply least-privilege access so users only have the permissions they need."
        }
    },
    {
        "id": 5,
        "risk": "Low",
        "status": "Open",
        "finding_type": "Logging",
        "resource_name": "audit-log-service",
        "manager_view": {
            "title": "Logging alert for audit-log-service",
            "situation": "Some security logs are not retained for the recommended duration.",
            "business_risk": "The team may have limited visibility when investigating past incidents or compliance questions.",
            "recommended_action": "Extend log retention and ensure audit logs are enabled for key cloud resources."
        }
    },
    {
        "id": 6,
        "risk": "Low",
        "status": "Resolved",
        "finding_type": "Access Review",
        "resource_name": "temporary-contractor-account",
        "manager_view": {
            "title": "Access Review alert for temporary-contractor-account",
            "situation": "A temporary contractor account was still active after the expected project access period.",
            "business_risk": "Inactive or outdated accounts can increase the chance of unauthorized access if not removed on time.",
            "recommended_action": "Confirm the user no longer needs access and remove or disable the account."
        }
    }
]

PRIORITY_ORDER = {
    "Danger": 1,
    "Warning": 2,
    "Low": 3
}

STATUS_COLORS = {
    "Open": "🔴",
    "In Progress": "🟠",
    "Resolved": "🟢"
}

# -----------------------------
# Styling
# -----------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: #f7fafc;
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

    .risk-level-low {
        background: #dcfce7;
        color: #166534 !important;
        border: 1px solid #bbf7d0;
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

    .sidebar-note {
        color: #cbd5e1 !important;
        font-size: 13px;
        line-height: 1.5;
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
    if risk == "Low":
        return "priority-low"
    return ""


def risk_level_class(risk):
    if risk == "Danger":
        return "risk-level-danger"
    if risk == "Warning":
        return "risk-level-warning"
    if risk == "Low":
        return "risk-level-low"
    return ""


def sort_security_findings(findings, sort_option):
    if sort_option == "Risk: Danger first":
        return sorted(findings, key=lambda x: PRIORITY_ORDER[x["risk"]])

    if sort_option == "Risk: Low first":
        return sorted(findings, key=lambda x: PRIORITY_ORDER[x["risk"]], reverse=True)

    if sort_option == "Finding Type A-Z":
        return sorted(findings, key=lambda x: x["finding_type"])

    if sort_option == "Status A-Z":
        return sorted(findings, key=lambda x: x["status"])

    return findings


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("🔐 CloudOps Security")
    st.caption("Manager View")

    st.divider()

    st.markdown("### Switch View")

    if st.button("⚡ Workload Manager", use_container_width=True):
        st.switch_page("workload-nontech.py")

    if st.button("🔐 Security Manager", use_container_width=True):
        st.switch_page("pages/security-nontech.py")

    st.divider()

    st.markdown("### View")
    st.info("You are currently viewing the **security-focused manager page**.")


# -----------------------------
# Main Page
# -----------------------------
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-title">Security Manager View 🔐</div>
        <div class="hero-subtitle">
            Review security findings in business-friendly language and view smart recommendations directly inside each card.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <h2 class="section-heading">Priority Tasks & Issues</h2>
    <div class="section-caption">
        Security findings are shown with manager-level explanations and smart recommendations.
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Filters
# -----------------------------
filter_col1, filter_col2, filter_col3 = st.columns([1.2, 1.2, 1.6])

with filter_col1:
    selected_finding_type = st.selectbox(
        "Filter by finding type",
        ["All", "Public Storage", "CVE", "Misconfiguration", "Identity Access", "Logging", "Access Review"],
        key="security_finding_type_filter"
    )

with filter_col2:
    selected_security_risk = st.selectbox(
        "Filter by risk",
        ["All", "Danger", "Warning", "Low"],
        key="security_risk_filter"
    )

with filter_col3:
    security_sort_option = st.selectbox(
        "Arrange tasks by",
        [
            "Risk: Danger first",
            "Risk: Low first",
            "Finding Type A-Z",
            "Status A-Z"
        ],
        key="security_sort_filter"
    )

# -----------------------------
# Apply Filters
# -----------------------------
filtered_findings = SECURITY_FINDINGS

if selected_finding_type != "All":
    filtered_findings = [
        finding for finding in filtered_findings
        if finding["finding_type"] == selected_finding_type
    ]

if selected_security_risk != "All":
    filtered_findings = [
        finding for finding in filtered_findings
        if finding["risk"] == selected_security_risk
    ]

filtered_findings = sort_security_findings(filtered_findings, security_sort_option)

# -----------------------------
# Security Cards
# -----------------------------
if not filtered_findings:
    st.warning("No security findings match the current filters.")
else:
    for finding in filtered_findings:
        manager_view = finding["manager_view"]

        card_html = f"""
<div class="security-card">
    <div class="security-topline">
        <div>
            <div class="security-title">🔐 {manager_view["title"]}</div>
            <div class="security-situation">{manager_view["situation"]}</div>
        </div>
        <div class="risk-level-box {risk_level_class(finding["risk"])}">
            {finding["risk"]}
            <span class="risk-level-label">Risk Level</span>
        </div>
    </div>
    <span class="pill {priority_class(finding["risk"])}">Risk: {finding["risk"]}</span>
    <span class="pill">Status: {STATUS_COLORS[finding["status"]]} {finding["status"]}</span>
    <span class="pill">Finding Type: {finding["finding_type"]}</span>
    <span class="pill">Resource: {finding["resource_name"]}</span>
    <div class="recommendation-box">
        <div class="recommendation-title">Business Risk</div>
        <div class="recommendation-text">{manager_view["business_risk"]}</div>
        <div class="recommendation-title">Smart Recommendation</div>
        <div class="smart-recommendation-box">
            <p>{manager_view["recommended_action"]}</p>
        </div>
    </div>
</div>
"""

        st.markdown(card_html, unsafe_allow_html=True)