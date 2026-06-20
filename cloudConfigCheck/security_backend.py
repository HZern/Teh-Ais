import json
import sys
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from config_scanner import scan_cloud_configurations


HOST = "127.0.0.1"
PORT = 8000
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
ML_RECOMMENDATIONS_FILE = PROJECT_DIR / "ml-pipeline" / "resource_recommendations.json"
AI_DIR = PROJECT_DIR / "ai"

if str(AI_DIR) not in sys.path:
    sys.path.append(str(AI_DIR))

from ai.sustainability_calculator import SustainabilityCalculator


def load_ml_recommendations():
    """
    Loads ML workload recommendations used by the workload manager dashboard.
    """
    with open(ML_RECOMMENDATIONS_FILE, "r") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("resource_recommendations.json must contain a list")

    return data


def workload_action_title(action):
    action_titles = {
        "schedule_auto_shutdown": "Idle cloud workload should be scheduled off",
        "downsize_instance": "Cloud workload can be right-sized",
        "increase_autoscaling_max": "Autoscaling capacity needs review",
        "decrease_autoscaling_min": "Minimum autoscaling capacity may be too high",
        "investigate_demand_spike": "Unexpected demand spike needs review",
        "no_action_needed": "Cloud workload is operating normally",
    }

    return action_titles.get(action, "Cloud workload recommendation")


def workload_priority(risk_level, action):
    if risk_level == "High":
        return "Danger"
    if risk_level == "Medium":
        return "Warning"
    if action == "no_action_needed":
        return "Low"
    return "Low"


def workload_impact(priority):
    if priority == "Danger":
        return "High"
    if priority == "Warning":
        return "Medium"
    return "Low"


def workload_risk_score(priority, annual_carbon_saved_kg):
    base_score = {
        "Danger": 86,
        "Warning": 72,
        "Low": 52,
    }.get(priority, 52)

    carbon_adjustment = min(int(annual_carbon_saved_kg), 12)
    return min(base_score + carbon_adjustment, 99)


def format_rm_from_usd(usd_value):
    if usd_value is None:
        return "N/A"

    # Hackathon dashboard display uses RM. Keep the conversion simple and local.
    rm_value = round(float(usd_value) * 4.7)
    return f"RM {rm_value:,}/month"


def format_carbon_saving(annual_carbon_saved_kg):
    monthly_kg = float(annual_carbon_saved_kg) / 12

    if monthly_kg >= 1000:
        return f"{monthly_kg / 1000:.1f} tCO2e/month"

    return f"{monthly_kg:.1f} kg CO2e/month"


def build_security_workload_tasks(alerts):
    tasks = []

    for alert in alerts:
        manager_view = alert.get("manager_view", {})
        priority = alert.get("finding_type", "Warning")

        tasks.append({
            "id": f"security-{alert.get('alert_id', alert.get('resource_name', len(tasks)))}",
            "title": manager_view.get("title", "Cloud security issue"),
            "risk_score": 92 if priority == "Danger" else 74,
            "category": "Cloud Security",
            "priority": priority,
            "status": "Open" if alert.get("status") == "FAILED" else "In Progress",
            "impact": "High" if priority == "Danger" else "Medium",
            "cost_saving": "N/A",
            "carbon_saving": "N/A",
            "summary": manager_view.get("situation", "Security scanner reported an issue."),
            "recommendation": [
                manager_view.get("recommended_action", "Ask the cloud team to review this issue."),
                f"Focus area: {manager_view.get('aws_part_to_fix', alert.get('area', 'AWS configuration'))}.",
                f"Resource to review: {alert.get('resource_name', 'Unknown resource')}.",
            ],
            "business_value": manager_view.get("business_risk", "Reduces business and operational cloud risk."),
            "source": "Cloud configuration scanner",
        })

    return tasks


def build_ml_workload_tasks():
    recommendations = load_ml_recommendations()
    sustainability_report = SustainabilityCalculator().aggregate_ml_recommendations(
        recommendations
    )
    tasks = []

    for index, report in enumerate(sustainability_report["top_recommendations"], start=1):
        action = report["suggested_action"]
        priority = workload_priority(report["risk_level"], action)
        annual_carbon_saved_kg = report["carbon"]["saved_kg_co2e_annual"]
        monthly_cost_saved = report["cost"]["saved_monthly"]
        current_cores = report["allocation"]["current_cores"]
        recommended_cores = report["allocation"]["recommended_cores"]
        vm_id = report["vm_id"]
        short_vm_id = vm_id[:10]

        tasks.append({
            "id": f"workload-{index}-{short_vm_id}",
            "title": workload_action_title(action),
            "risk_score": workload_risk_score(priority, annual_carbon_saved_kg),
            "category": "Energy Efficiency" if action != "no_action_needed" else "Sustainability",
            "priority": priority,
            "status": "Open" if action != "no_action_needed" else "Resolved",
            "impact": workload_impact(priority),
            "cost_saving": format_rm_from_usd(monthly_cost_saved),
            "carbon_saving": format_carbon_saving(annual_carbon_saved_kg),
            "summary": report["explainability"].get(
                "rationale",
                "ML workload analysis found an optimization opportunity.",
            ),
            "recommendation": [
                f"Review VM {short_vm_id} in {report['carbon']['aws_region']}.",
                f"Current allocation is {current_cores:g} cores; recommended allocation is {recommended_cores:g} cores.",
                "Apply the recommended scheduling or rightsizing change during a low-risk maintenance window.",
            ],
            "business_value": (
                "Reduces avoidable cloud spend and Scope 3 cloud services emissions while keeping "
                "construction technology workloads aligned with actual demand."
            ),
            "source": "ML sustainability recommendation pipeline",
        })

    return tasks


def build_workload_tasks():
    alerts = scan_cloud_configurations()
    tasks = build_security_workload_tasks(alerts) + build_ml_workload_tasks()

    tasks.sort(key=lambda task: task["risk_score"], reverse=True)
    return tasks


def build_co2_timeseries(days=30):
    recommendations = load_ml_recommendations()
    calculator = SustainabilityCalculator()

    daily_co2_kg = 0.0
    for recommendation in recommendations:
        region = recommendation.get(
            "aws_region",
            calculator.constants.default_hilti_aws_region
        )
        wasted_kwh_day = float(
            recommendation.get("estimated_wasted_energy_kwh_per_day", 0.0)
        )
        daily_co2_kg += wasted_kwh_day * calculator._carbon_intensity(region)

    end_date = datetime.now().date()
    points = []

    for day_index in range(days):
        point_date = end_date - timedelta(days=days - day_index - 1)
        weekday_factor = 1 + ((point_date.weekday() - 3) * 0.025)
        trend_factor = 1 + ((day_index - days + 1) * 0.003)
        co2_kg = max(daily_co2_kg * weekday_factor * trend_factor, 0.0)

        points.append({
            "date": point_date.isoformat(),
            "co2_kg": round(co2_kg, 2),
        })

    return {
        "points": points,
        "count": len(points),
        "message": (
            "Estimated CO2e produced from avoidable cloud workload waste over "
            f"the last {days} days"
        ),
        "unit": "kg CO2e",
        "method": (
            "estimated_wasted_energy_kwh_per_day multiplied by AWS regional "
            "carbon intensity; trend is generated from current ML workload data"
        ),
    }


class SecurityBackendHandler(BaseHTTPRequestHandler):
    """
    Simple backend server for the cloud security monitoring MVP.

    Routes:
    - GET /        : health check
    - GET /alerts  : runs scanner and returns latest warning/danger alerts
    - GET /workload-tasks : returns manager-ready workload dashboard tasks
    - GET /co2-timeseries : returns workload CO2e trend data for the dashboard
    """

    def send_json_response(self, data, status_code=200):
        """
        Sends a JSON response with CORS enabled so the frontend can call it.
        """
        response = json.dumps(data, indent=4)

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

        self.wfile.write(response.encode("utf-8"))

    def do_OPTIONS(self):
        """
        Handles browser CORS preflight requests.
        """
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """
        Handles GET requests from the frontend.
        """
        if self.path == "/":
            self.send_json_response({
                "message": "Cloud Security Monitoring Backend is running"
            })

        elif self.path == "/alerts":
            alerts = scan_cloud_configurations()

            self.send_json_response({
                "alerts": alerts,
                "count": len(alerts),
                "message": "Scanner ran successfully and returned latest alerts"
            })

        elif self.path == "/workload-tasks":
            tasks = build_workload_tasks()

            self.send_json_response({
                "tasks": tasks,
                "count": len(tasks),
                "message": "Workload tasks built from scanner and ML recommendation backend data"
            })

        elif self.path == "/co2-timeseries":
            self.send_json_response(build_co2_timeseries())

        else:
            self.send_json_response({
                "error": "Endpoint not found"
            }, status_code=404)


def run_backend():
    """
    Starts the local backend server.
    """
    server = HTTPServer((HOST, PORT), SecurityBackendHandler)

    print(f"Security backend running at http://{HOST}:{PORT}")
    print(f"Alerts endpoint: http://{HOST}:{PORT}/alerts")
    print(f"Workload tasks endpoint: http://{HOST}:{PORT}/workload-tasks")
    print(f"CO2 timeseries endpoint: http://{HOST}:{PORT}/co2-timeseries")

    server.serve_forever()


if __name__ == "__main__":
    run_backend()
