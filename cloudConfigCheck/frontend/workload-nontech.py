import streamlit as st
from datetime import datetime
from textwrap import dedent

# ==========================================================
# Hackathon Frontend Prototype
# Manager / Non-Technical View
# Secure & Energy-Aware Cloud Platform for Construction Tech
# ==========================================================

st.set_page_config(
    page_title="CloudOps Manager Dashboard",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Dummy Data
# Replace this later with API/database/cloud monitoring data
# -----------------------------
TASKS = [
    {
        "id": 1,
        "title": "Idle cloud servers detected",
        "risk_score": 96,
        "category": "Energy Efficiency",
        "priority": "Danger",
        "status": "Open",
        "impact": "High",
        "cost_saving": "RM 4,200/month",
        "carbon_saving": "1.8 tCO₂e/month",
        "summary": "Several compute instances have been running below 5% CPU usage for more than 14 days.",
        "recommendation": [
            "Shut down unused instances outside working hours.",
            "Move low-usage servers to smaller instance types.",
            "Enable auto-scaling rules based on actual construction workload demand."
        ],
        "business_value": "Reduces unnecessary cloud cost and lowers energy consumption without affecting active project work."
    },
    {
        "id": 2,
        "title": "Public storage bucket contains project files",
        "risk_score": 94,
        "category": "Cloud Security",
        "priority": "Danger",
        "status": "Open",
        "impact": "High",
        "cost_saving": "N/A",
        "carbon_saving": "N/A",
        "summary": "A cloud storage bucket containing BIM/project documents is publicly accessible.",
        "recommendation": [
            "Disable public access immediately.",
            "Apply role-based access control for project teams.",
            "Enable audit logging to track future access changes."
        ],
        "business_value": "Reduces the risk of data leakage, project confidentiality breaches, and compliance issues."
    },
    {
        "id": 3,
        "title": "Database server missing latest security patch",
        "risk_score": 82,
        "category": "Cloud Security",
        "priority": "Warning",
        "status": "In Progress",
        "impact": "Medium",
        "cost_saving": "N/A",
        "carbon_saving": "N/A",
        "summary": "A known CVE affects the current database version used for operational data.",
        "recommendation": [
            "Schedule patching during low-traffic hours.",
            "Create a backup before applying the update.",
            "Re-scan after patching to confirm the vulnerability is resolved."
        ],
        "business_value": "Improves cloud security posture while reducing the risk of system compromise."
    },
    {
        "id": 4,
        "title": "High carbon workload running during peak grid hours",
        "risk_score": 79,
        "category": "Sustainability",
        "priority": "Warning",
        "status": "Open",
        "impact": "High",
        "cost_saving": "RM 1,100/month",
        "carbon_saving": "0.9 tCO₂e/month",
        "summary": "Large batch-processing jobs are running during periods with higher estimated grid carbon intensity.",
        "recommendation": [
            "Move non-urgent workloads to lower-carbon time windows.",
            "Prioritize renewable-energy regions where possible.",
            "Create a carbon-aware scheduling policy."
        ],
        "business_value": "Supports ESG reporting and reduces the environmental impact of cloud operations."
    },
    {
        "id": 5,
        "title": "Over-provisioned Kubernetes cluster",
        "risk_score": 64,
        "category": "Energy Efficiency",
        "priority": "Low",
        "status": "Open",
        "impact": "Medium",
        "cost_saving": "RM 2,000/month",
        "carbon_saving": "0.7 tCO₂e/month",
        "summary": "Cluster resource requests are much higher than actual workload usage.",
        "recommendation": [
            "Right-size CPU and memory requests.",
            "Enable cluster autoscaler.",
            "Review workload limits every week."
        ],
        "business_value": "Improves resource efficiency and reduces unnecessary infrastructure spending."
    },
    {
        "id": 6,
        "title": "No sustainability visibility for project cloud usage",
        "risk_score": 58,
        "category": "Sustainability",
        "priority": "Low",
        "status": "Open",
        "impact": "Medium",
        "cost_saving": "N/A",
        "carbon_saving": "Reporting improvement",
        "summary": "Cloud energy and emissions are not clearly mapped to each construction project.",
        "recommendation": [
            "Tag cloud resources by project name and department.",
            "Generate monthly Scope-related cloud emissions summaries.",
            "Add sustainability KPIs to management reporting."
        ],
        "business_value": "Improves ESG visibility and helps managers understand the environmental impact of cloud usage."
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

CATEGORY_ICONS = {
    "Cloud Security": "🔐",
    "Energy Efficiency": "⚡",
    "Sustainability": "🌱"
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

    .card-control-label {
        color: #475569 !important;
        font-size: 13px;
        font-weight: 750;
        margin-bottom: 4px;
    }

    .card-control-note {
        color: #64748b !important;
        font-size: 12px;
        margin-top: -4px;
        margin-bottom: 6px;
    }

    label, 
    [data-testid="stWidgetLabel"] p {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.task-card-marker) {
        background: #ffffff !important;
        border: 1.5px solid #dbe3ee !important;
        border-radius: 18px !important;
        padding: 18px !important;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08) !important;
        margin-bottom: 22px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"]:has(.task-card-marker):hover {
        border-color: #38bdf8 !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12) !important;
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

    .hero-card {
        padding: 24px;
        border-radius: 18px;
        background: linear-gradient(135deg, #0f172a 0%, #0e7490 100%);
        color: white;
        margin-bottom: 22px;
    }

    .hero-title {
        font-size: 34px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .hero-subtitle {
        font-size: 17px;
        opacity: 0.92;
    }

    .metric-card {
        background: #ffffff;
        padding: 20px;
        border-radius: 16px;
        border: 2px solid #cbd5e1;
        border-top: 5px solid #0e7490;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.14);
        min-height: 120px;
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

    .section-heading {
        color: #0f172a !important;
        font-size: 26px;
        font-weight: 850;
        margin-top: 28px;
        margin-bottom: 12px;
    }

    .section-caption {
        color: #475569 !important;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 18px;
    }

    .task-card {
        background: white;
        padding: 20px;
        border-radius: 18px;
        border: 1px solid #dbe3ee;
        box-shadow: 0 2px 12px rgba(15, 23, 42, 0.08);
        margin-bottom: 12px;
        transition: 0.18s ease;
    }

    .task-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.12);
        border-color: #38bdf8;
    }

    .task-title {
        font-size: 20px;
        font-weight: 750;
        color: #0f172a !important;
        margin-bottom: 6px;
    }

    .task-summary {
    color: #475569 !important;
    font-size: 15px;
    margin-bottom: 10px;
    line-height: 1.5;
    }

    .risk-topline {
        display: flex;
        justify-content: space-between;
        align-items: start;
        gap: 14px;
    }

    .risk-level-box {
        min-width: 96px;
        text-align: center;
        padding: 12px 14px;
        border-radius: 14px;
        font-weight: 850;
        font-size: 16px;
        margin: 6px 8px 6px 8px;
    }

    .risk-level-label {
        display: block;
        font-size: 11px;
        font-weight: 650;
        margin-top: 3px;
    }

    .risk-level-danger {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }

    .risk-level-warning {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    .risk-level-low {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    .risk-score {
        min-width: 76px;
        text-align: center;
        padding: 9px 10px;
        border-radius: 14px;
        background: #0f172a;
        color: white !important;
        font-weight: 800;
        font-size: 18px;
    }

    .risk-score-label {
        display: block;
        font-size: 11px;
        color: #cbd5e1 !important;
        font-weight: 600;
        margin-top: 2px;
    }

    .pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #e0f2fe;
        color: #075985;
        font-size: 13px;
        font-weight: 650;
        margin-right: 6px;
        margin-bottom: 6px;
    }

    .priority-danger {
        background: #fee2e2;
        color: #991b1b;
    }

    .priority-warning {
        background: #fef3c7;
        color: #92400e;
    }

    .priority-low {
        background: #dcfce7;
        color: #166534;
    }

    .recommendation-card {
        background: #ffffff;
        color: #0f172a !important;
        padding: 24px;
        border-radius: 18px;
        border: 1px solid #dbe3ee;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.10);
    }

    .recommendation-card h2,
    .recommendation-card h3,
    .recommendation-card p {
        color: #0f172a !important;
    }

    .recommendation-card p {
        font-size: 15px;
        line-height: 1.5;
    }

    .manager-summary-text {
        color: #334155 !important;
        font-size: 15px;
        line-height: 1.6;
    }

    .action-card {
        background: #dcfce7;
        color: #14532d !important;
        padding: 16px 18px;
        border-radius: 12px;
        border-left: 5px solid #22c55e;
        margin-bottom: 12px;
        font-weight: 650;
    }

    .next-step-card {
        background: #dbeafe;
        color: #1e3a8a !important;
        padding: 18px;
        border-radius: 14px;
        border-left: 5px solid #3b82f6;
        margin-top: 24px;
        font-weight: 650;
        line-height: 1.6;
    }

    .next-step-card p,
    .next-step-card div,
    .next-step-card span {
        color: #1e3a8a !important;
    }

    .small-muted {
        color: #64748b;
        font-size: 14px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Helper Functions
# -----------------------------
def sort_tasks(tasks, sort_option):
    if sort_option == "Risk: Danger first":
        return sorted(tasks, key=lambda x: (PRIORITY_ORDER[x["priority"]], -x["risk_score"]))

    if sort_option == "Risk: Low first":
        return sorted(tasks, key=lambda x: (PRIORITY_ORDER[x["priority"]], -x["risk_score"]), reverse=True)

    if sort_option == "Highest cost saving":
        def cost_value(task):
            value = task["cost_saving"]
            if value == "N/A":
                return 0
            return int(value.replace("RM", "").replace(",", "").replace("/month", "").strip())

        return sorted(tasks, key=cost_value, reverse=True)

    if sort_option == "Category A-Z":
        return sorted(tasks, key=lambda x: x["category"])

    return tasks


def priority_class(priority):
    if priority == "Danger":
        return "priority-danger"
    if priority == "Warning":
        return "priority-warning"
    if priority == "Low":
        return "priority-low"
    return ""


def risk_level_class(priority):
    if priority == "Danger":
        return "risk-level-danger"
    if priority == "Warning":
        return "risk-level-warning"
    if priority == "Low":
        return "risk-level-low"
    return ""


def get_task_by_id(task_id):
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            return task
    return None


def update_task_risk(task_id, widget_key):
    new_risk = st.session_state[widget_key]

    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["priority"] = new_risk
            break


def go_to_recommendation(task_id):
    st.session_state.selected_task_id = task_id
    st.session_state.page = "recommendation"


def go_home():
    st.session_state.page = "dashboard"
    st.session_state.selected_task_id = None


# -----------------------------
# Session State Routing
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None

if "tasks" not in st.session_state:
    st.session_state.tasks = TASKS.copy()


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("☁️ CloudOps")
    st.caption("Manager View")

    st.divider()

    st.markdown("### Switch View")

    if st.button("⚡ Workload Manager", use_container_width=True):
        st.switch_page("workload-nontech.py")

    if st.button("🔐 Security Manager", use_container_width=True):
        st.switch_page("pages/security-nontech.py")

    st.divider()

    st.markdown("### View")
    st.info("You are currently viewing the **workload-focused manager page**.")


# -----------------------------
# Dashboard Page
# -----------------------------
if st.session_state.page == "dashboard":
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Good afternoon, Project Manager 👋</div>
            <div class="hero-subtitle">
                Here is today’s overview of cloud security, energy efficiency, and sustainability issues across your construction technology environment.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    tasks = st.session_state.tasks

    danger_count = len([t for t in tasks if t["priority"] == "Danger"])
    warning_count = len([t for t in tasks if t["priority"] == "Warning"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Danger Tasks</div>
                <div class="metric-number">{danger_count}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Warning Tasks</div>
                <div class="metric-number">{warning_count}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        """
    <h2 class="section-heading">Priority Tasks & Issues</h2>
    <div class="section-caption">Click any issue to view the smart recommendation page.</div>
        """,
        unsafe_allow_html=True
    )

    filter_col1, filter_col2, filter_col3 = st.columns([1.2, 1.2, 1.6])

    with filter_col1:
        selected_category = st.selectbox(
            "Filter by category",
            ["All", "Cloud Security", "Energy Efficiency", "Sustainability"]
        )

    with filter_col2:
        selected_priority = st.selectbox(
            "Filter by risk",
            ["All", "Danger", "Warning", "Low"]
        )

    with filter_col3:
        sort_option = st.selectbox(
            "Arrange tasks by",
            [
                "Risk: Danger first",
                "Risk: Low first",
                "Highest cost saving",
                "Category A-Z"
            ]
        )

    filtered_tasks = st.session_state.tasks

    if selected_category != "All":
        filtered_tasks = [t for t in filtered_tasks if t["category"] == selected_category]

    if selected_priority != "All":
        filtered_tasks = [t for t in filtered_tasks if t["priority"] == selected_priority]

    filtered_tasks = sort_tasks(filtered_tasks, sort_option)

    if not filtered_tasks:
        st.warning("No tasks match the current filters.")
    else:
        for task in filtered_tasks:
            with st.container(border=True):
                st.markdown('<div class="task-card-marker"></div>', unsafe_allow_html=True)

                top_left, top_right = st.columns([6, 1])

                with top_left:
                    st.markdown(
                        f"""
    <div class="task-title">{CATEGORY_ICONS[task["category"]]} {task["title"]}</div>
    <div class="task-summary">{task["summary"]}</div>
                        """,
                        unsafe_allow_html=True
                    )

                with top_right:
                    st.markdown(
                        f"""
                <div class="risk-level-box {risk_level_class(task["priority"])}">
                    {task["priority"]}
                    <span class="risk-level-label">Risk Level</span>
                </div>
                        """,
                        unsafe_allow_html=True
                    )

                badge_html = f"""
                <span class="pill {priority_class(task["priority"])}">Risk: {task["priority"]}</span>
                <span class="pill">Status: {STATUS_COLORS[task["status"]]} {task["status"]}</span>
                <span class="pill">Category: {task["category"]}</span>
                <span class="pill">Impact: {task["impact"]}</span>
                <span class="pill">Risk Score: {task["risk_score"]}/100</span>
                <span class="pill">Cost Saving: {task["cost_saving"]}</span>
                <span class="pill">Carbon Saving: {task["carbon_saving"]}</span>
                """
                st.markdown(badge_html, unsafe_allow_html=True)

                st.divider()

                control_col1, control_col2 = st.columns([1.3, 4])

                with control_col1:
                    st.markdown(
                        """
    <div class="card-control-label">Manager Risk</div>
    <div class="card-control-note">Change risk level</div>
                        """,
                        unsafe_allow_html=True
                    )

                    risk_key = f"risk_override_{task['id']}"

                    risk_options = ["Danger", "Warning", "Low"]

                    st.selectbox(
                        "Manager Risk",
                        risk_options,
                        index=risk_options.index(task["priority"]),
                        key=risk_key,
                        on_change=update_task_risk,
                        args=(task["id"], risk_key),
                        label_visibility="collapsed"
                    )

                with control_col2:
                    st.markdown(
                        """
    <div class="card-control-label">&nbsp;</div>
    <div class="card-control-note">&nbsp;</div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.button(
                        "View smart recommendation →",
                        key=f"task_{task['id']}",
                        on_click=go_to_recommendation,
                        args=(task["id"],),
                        use_container_width=True
                    )

# -----------------------------
# Smart Recommendation Page
# -----------------------------
elif st.session_state.page == "recommendation":
    task = get_task_by_id(st.session_state.selected_task_id)

    if task is None:
        st.error("Task not found.")
        if st.button("Back to dashboard"):
            go_home()
    else:
        st.button("← Back to dashboard", on_click=go_home)

        st.markdown(
            f"""
            <div class="hero-card">
                <div class="hero-title">Smart Recommendation</div>
                <div class="hero-subtitle">
                    Recommended action plan for: {task["title"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        left, right = st.columns([1.4, 1])

        with left:
            recommendation_html = f"""
        <div class="recommendation-card">
            <h2>{CATEGORY_ICONS[task["category"]]} {task["title"]}</h2>
            <p>{task["summary"]}</p>
            <span class="pill {priority_class(task["priority"])}">Risk: {task["priority"]}</span>
            <span class="pill">Status: {STATUS_COLORS[task["status"]]} {task["status"]}</span>
            <span class="pill">Category: {task["category"]}</span>
            <span class="pill">Impact: {task["impact"]}</span>
            <span class="pill">Risk Score: {task["risk_score"]}/100</span>
            <h3 style="margin-top: 22px;">Recommended Actions</h3>
        </div>
        """
            st.markdown(recommendation_html, unsafe_allow_html=True)

            for index, item in enumerate(task["recommendation"], start=1):
                action_html = f"""
        <div class="action-card">
            {index}. {item}
        </div>
        """
                st.markdown(action_html, unsafe_allow_html=True)

        with right:
            summary_html = f"""
        <div class="recommendation-card">
            <h3>Manager Summary</h3>
            <div class="manager-summary-text">
                <p><b>Business value:</b><br>{task["business_value"]}</p>
                <p><b>Estimated cost saving:</b><br>{task["cost_saving"]}</p>
                <p><b>Estimated carbon saving:</b><br>{task["carbon_saving"]}</p>
                <p><b>Last updated:</b><br>{datetime.now().strftime("%d %b %Y, %I:%M %p")}</p>
            </div>
        </div>
        """
            st.markdown(summary_html, unsafe_allow_html=True)

        st.markdown(
            """
            <h2 class="section-heading">Suggested Next Step</h2>
            """,
            unsafe_allow_html=True
        )

        next_step_html = """
        <div class="next-step-card">
            <p>
                For the hackathon prototype, this recommendation can later be generated using rules or AI based on cloud usage metrics, security scan results, cost data, and carbon estimation data.
            </p>
        </div>
        """

        st.markdown(next_step_html, unsafe_allow_html=True)
