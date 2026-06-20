import json
from pathlib import Path
from datetime import datetime
from rules.s3_rules import check_s3_security_baseline
from rules.security_group_rules import check_security_group_ssh_baseline 
from rules.iam_rules import check_iam_user_baseline

## Directories
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "sample_s3_buckets.json"
SECURITY_GROUP_DATA_FILE = BASE_DIR / "data" / "sample_security_groups.json"
IAM_DATA_FILE = BASE_DIR / "data" / "sample_iam_users.json"


# Load s3 buckets
def load_s3_buckets():
    """
    Loads the sample AWS-style S3 bucket configuration data.
    """
    with open(DATA_FILE, "r") as file:
        return json.load(file)

# Load security groups
def load_security_groups():
    """
    Loads sample AWS-style EC2 Security Group configuration data.
    """
    with open(SECURITY_GROUP_DATA_FILE, "r") as file:
        return json.load(file)

# Load iam users
def load_iam_users():
    """
    Loads sample AWS-style IAM user configuration data.
    """
    with open(IAM_DATA_FILE, "r") as file:
        return json.load(file)

def run_checks():
    """
    Runs all cloud security baseline checks.
    """
    findings = []

    s3_buckets = load_s3_buckets()
    for bucket in s3_buckets:
        findings.append(check_s3_security_baseline(bucket))

    security_groups = load_security_groups()
    for security_group in security_groups:
        findings.append(check_security_group_ssh_baseline(security_group))

    iam_users = load_iam_users()
    for user in iam_users:
        findings.append(check_iam_user_baseline(user))

    return findings

def prepare_website_alerts(findings):
    """
    Prepares only warning and danger findings for the website.

    Safe findings are not included because the website alert panel
    should only display resources that need attention.
    """
    website_alerts = []

    for finding in findings:
        if finding["severity"] == "NONE":
            continue

        alert = {
            "alert_id": f"{finding['resource_name']}-{finding['severity'].lower()}",
            "generated_at": datetime.now().isoformat(),

            # Basic display info
            "team": finding["team"],
            "area": finding["area"],
            "resource_name": finding["resource_name"],
            "resource_type": finding["resource_type"],

            # Alert status
            "status": finding["status"],
            "severity": finding["severity"],
            "finding_type": finding["finding_type"],

            # Manager-level display
            "manager_view": {
                "title": f"{finding['finding_type']} alert for {finding['resource_name']}",
                "situation": finding["reason"],
                "business_risk": finding["risk"],
                "recommended_action": finding["manager_recommendation"]
            },

            # Technician-level display
            "technician_view": {
                "resource_id": finding["resource_id"],
                "rule": finding["rule"],
                "technical_reason": finding["reason"],
                "technical_fix": finding["technician_recommendation"]
            }
        }

        website_alerts.append(alert)

    return website_alerts


def print_website_alerts(website_alerts):
    """
    Prints the prepared website output variables for testing.
    This simulates what will later be sent to the frontend.
    """
    print("\nPrepared Website Alert Variables")
    print("=" * 60)

    if not website_alerts:
        print("No warning or danger alerts found.")
        return

    for alert in website_alerts:
        print(f"\nAlert ID: {alert['alert_id']}")
        print(f"Generated At: {alert['generated_at']}")
        print(f"Team: {alert['team']}")
        print(f"Area: {alert['area']}")
        print(f"Resource Name: {alert['resource_name']}")
        print(f"Resource Type: {alert['resource_type']}")
        print(f"Status: {alert['status']}")
        print(f"Severity: {alert['severity']}")
        print(f"Finding Type: {alert['finding_type']}")

        print("\nManager View")
        print("-" * 30)
        print(f"Title: {alert['manager_view']['title']}")
        print(f"Situation: {alert['manager_view']['situation']}")
        print(f"Business Risk: {alert['manager_view']['business_risk']}")
        print(f"Recommended Action: {alert['manager_view']['recommended_action']}")

        print("\nTechnician View")
        print("-" * 30)
        print(f"Resource ID: {alert['technician_view']['resource_id']}")
        print(f"Rule: {alert['technician_view']['rule']}")
        print(f"Technical Reason: {alert['technician_view']['technical_reason']}")
        print(f"Technical Fix: {alert['technician_view']['technical_fix']}")


if __name__ == "__main__":
    findings = run_checks()

    website_alerts = prepare_website_alerts(findings)

    print_website_alerts(website_alerts)