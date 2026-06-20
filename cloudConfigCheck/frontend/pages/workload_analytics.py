import streamlit as st
import requests
from datetime import datetime

# ==========================================================
# Hackathon Frontend Prototype
# Manager / Non-Technical View
# Secure & Energy-Aware Cloud Platform for Construction Tech
# ==========================================================

st.set_page_config(
    page_title="CloudOps Manager Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Backend Data
# -----------------------------
API_URL = "http://127.0.0.1:8000/workload-tasks"

PRIORITY_ORDER = {
    "Danger": 1,
    "Warning": 2,
    "Low": 3
}

PRIORITY_DISPLAY_LABELS = {
    "Danger": "High",
    "Warning": "Medium",
    "Low": "Low"
}

PRIORITY_FILTER_VALUES = {
    "All": "All",
    "High": "Danger",
    "Medium": "Warning",
    "Low": "Low"
}

STATUS_COLORS = {
    "Open": "🔴",
    "In Progress": "🟠",
    "Resolved": "🟢"
}

@st.cache_data(ttl=10)
def fetch_workload_tasks():
    try:
        response = requests.get(API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()

        return {
            "tasks": data.get("tasks", []),
            "count": data.get("count", 0),
            "message": data.get("message", "Backend returned workload tasks"),
            "error": None,
            "last_updated": datetime.now().strftime("%I:%M:%S %p")
        }

    except requests.exceptions.RequestException as error:
        return {
            "tasks": [],
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

    div[data-testid="stButton"] > button {
        background-color: #111827 !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }

    div[data-testid="stButton"] > button:hover {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
    }

    div[data-testid="stButton"] > button p {
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 16px !important;
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
        font-size: 16px;
    }

    div[data-testid="stVerticalBlock"] {
        color: #0f172a !important;
    }

    p, span, div, label {
        color: inherit;
    }
    .main {
        background-color: #f7fafc;
    }

    [data-testid="stSidebarNav"] {
        display: none;
    }

    label, 
    [data-testid="stWidgetLabel"] p {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 16px !important;
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
        font-size: 16px !important;
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
        font-size: 36px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .hero-subtitle {
        font-size: 18px;
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
        font-size: 15px;
        font-weight: 750;
        margin-bottom: 10px;
    }

    .metric-number {
        color: #020617 !important;
        font-size: 38px;
        font-weight: 900;
        line-height: 1.1;
    }

    .chart-panel {
        background: #ffffff;
        border: 1.5px solid #dbe3ee;
        border-radius: 18px;
        padding: 18px 18px 8px 18px;
        box-shadow: 0 4px 16px rgba(15, 23, 42, 0.08);
        margin-bottom: 22px;
    }

    .section-heading {
        color: #0f172a !important;
        font-size: 28px;
        font-weight: 850;
        margin-top: 28px;
        margin-bottom: 12px;
    }

    .section-caption {
        color: #475569 !important;
        font-size: 17px;
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
        font-size: 22px;
        font-weight: 750;
        color: #0f172a !important;
        margin-bottom: 6px;
    }

    .task-summary {
    color: #475569 !important;
    font-size: 16px;
    margin-bottom: 10px;
    line-height: 1.5;
    }

    .priority-topline {
        display: flex;
        justify-content: space-between;
        align-items: start;
        gap: 14px;
    }

    .priority-level-box {
        min-width: 96px;
        text-align: center;
        padding: 12px 14px;
        border-radius: 14px;
        font-weight: 850;
        font-size: 18px;
        margin: 6px 8px 6px 8px;
    }

    .priority-level-label {
        display: block;
        font-size: 12px;
        font-weight: 650;
        margin-top: 3px;
    }

    .priority-level-danger {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }

    .priority-level-warning {
        background: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }

    .priority-level-low {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    .priority-score {
        min-width: 76px;
        text-align: center;
        padding: 9px 10px;
        border-radius: 14px;
        background: #0f172a;
        color: white !important;
        font-weight: 800;
        font-size: 20px;
    }

    .priority-score-label {
        display: block;
        font-size: 12px;
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
        font-size: 14px;
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
        font-size: 16px;
        line-height: 1.5;
    }

    .manager-summary-text {
        color: #334155 !important;
        font-size: 16px;
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
        font-size: 16px;
    }

    .action-card-first {
        margin-top: 24px;
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
        font-size: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Helper Functions
# -----------------------------
def sort_tasks(tasks, sort_option):
    if sort_option == "Priority: High first":
        return sorted(tasks, key=lambda x: (PRIORITY_ORDER.get(x["priority"], 99), -x["risk_score"]))

    if sort_option == "Priority: Low first":
        return sorted(
            tasks,
            key=lambda x: (PRIORITY_ORDER.get(x["priority"], 99), -x["risk_score"]),
            reverse=True
        )

    if sort_option == "Highest cost saving":
        def cost_value(task):
            value = str(task["cost_saving"])
            if value == "N/A":
                return 0
            cleaned_value = (
                value.replace("RM", "")
                .replace(",", "")
                .replace("/month", "")
                .strip()
            )
            try:
                return int(float(cleaned_value))
            except ValueError:
                return 0

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


def priority_level_class(priority):
    if priority == "Danger":
        return "priority-level-danger"
    if priority == "Warning":
        return "priority-level-warning"
    if priority == "Low":
        return "priority-level-low"
    return ""


def priority_label(priority):
    return PRIORITY_DISPLAY_LABELS.get(priority, priority)


def get_task_by_id(task_id):
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            return task
    return None


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

backend_result = fetch_workload_tasks()
st.session_state.tasks = backend_result["tasks"]


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("CloudOps")
    st.caption("Manager View")

    st.divider()

    st.markdown("### Switch View")

    if st.button("Workload Manager", use_container_width=True):
        st.switch_page("pages/workload_analytics.py")

    if st.button("🔐 Cloud Configuration Check", use_container_width=True):
        st.switch_page("pages/security_check.py")

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
            <div class="hero-title">Good afternoon, Project Manager</div>
            <div class="hero-subtitle">
                Here is today’s overview of energy efficiency issues across your construction technology environment.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

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

    tasks = st.session_state.tasks

    danger_count = len([t for t in tasks if t["priority"] == "Danger"])
    warning_count = len([t for t in tasks if t["priority"] == "Warning"])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">High Tasks</div>
                <div class="metric-number">{danger_count}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Medium Tasks</div>
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

    filter_col1, filter_col2 = st.columns([1.2, 1.6])

    with filter_col1:
        selected_priority = st.selectbox(
            "Filter by priority",
            ["All", "High", "Medium", "Low"]
        )

    with filter_col2:
        sort_option = st.selectbox(
            "Arrange tasks by",
            [
                "Priority: High first",
                "Priority: Low first",
                "Highest cost saving",
                "Category A-Z"
            ]
        )

    filtered_tasks = st.session_state.tasks

    if selected_priority != "All":
        selected_priority_value = PRIORITY_FILTER_VALUES[selected_priority]
        filtered_tasks = [t for t in filtered_tasks if t["priority"] == selected_priority_value]

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
    <div class="task-title">{task["title"]}</div>
    <div class="task-summary">{task["summary"]}</div>
                        """,
                        unsafe_allow_html=True
                    )

                with top_right:
                    st.markdown(
                        f"""
                <div class="priority-level-box {priority_level_class(task["priority"])}">
                    {priority_label(task["priority"])}
                    <span class="priority-level-label">Priority Level</span>
                </div>
                        """,
                        unsafe_allow_html=True
                    )

                badge_html = f"""
                <span class="pill {priority_class(task["priority"])}">Priority: {priority_label(task["priority"])}</span>
                <span class="pill">Status: {STATUS_COLORS.get(task["status"], "🔵")} {task["status"]}</span>
                <span class="pill">Category: {task["category"]}</span>
                <span class="pill">Impact: {task["impact"]}</span>
                <span class="pill">Priority Score: {task["risk_score"]}/100</span>
                <span class="pill">Cost Saving: {task["cost_saving"]}</span>
                <span class="pill">Carbon Saving: {task["carbon_saving"]}</span>
                """
                st.markdown(badge_html, unsafe_allow_html=True)

                st.divider()

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
            <h2>{task["title"]}</h2>
            <p>{task["summary"]}</p>
            <span class="pill {priority_class(task["priority"])}">Priority: {priority_label(task["priority"])}</span>
            <span class="pill">Status: {STATUS_COLORS.get(task["status"], "🔵")} {task["status"]}</span>
            <span class="pill">Category: {task["category"]}</span>
            <span class="pill">Impact: {task["impact"]}</span>
            <span class="pill">Priority Score: {task["risk_score"]}/100</span>
            <h3 style="margin-top: 22px;">Recommended Actions</h3>
        </div>
        """
            st.markdown(recommendation_html, unsafe_allow_html=True)

            for index, item in enumerate(task["recommendation"], start=1):
                action_class = "action-card action-card-first" if index == 1 else "action-card"
                action_html = f"""
        <div class="{action_class}">
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
                <p><b>Backend source:</b><br>{task.get("source", "CloudOps backend")}</p>
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
                This recommendation is generated from backend cloud configuration scan results and ML sustainability recommendations. Ask the cloud or IT team to review the listed resource and confirm the change window.
            </p>
        </div>
        """

        st.markdown(next_step_html, unsafe_allow_html=True)
