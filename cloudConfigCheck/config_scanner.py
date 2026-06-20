import json
from pathlib import Path
from datetime import datetime

from rules.s3_rules import check_s3_security_baseline
from rules.security_group_rules import check_security_group_ssh_baseline
from rules.iam_rules import check_iam_user_baseline
from rules.rds_rules import check_rds_database_baseline
from rules.cloudtrail_rules import check_cloudtrail_baseline
from rules.public_endpoint_rules import check_public_endpoint_baseline
from rules.lambda_rules import check_lambda_role_baseline


# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# Sample AWS-style configuration data files
S3_DATA_FILE = BASE_DIR / "data" / "sample_s3_buckets.json"
SECURITY_GROUP_DATA_FILE = BASE_DIR / "data" / "sample_security_groups.json"
IAM_DATA_FILE = BASE_DIR / "data" / "sample_iam_users.json"
RDS_DATA_FILE = BASE_DIR / "data" / "sample_rds_databases.json"
CLOUDTRAIL_DATA_FILE = BASE_DIR / "data" / "sample_cloudtrail.json"
PUBLIC_ENDPOINT_DATA_FILE = BASE_DIR / "data" / "sample_public_endpoints.json"
LAMBDA_DATA_FILE = BASE_DIR / "data" / "sample_lambda_functions.json"


def load_json_file(file_path):
    """
    Loads JSON data from a given file path.
    """
    with open(file_path, "r") as file:
        return json.load(file)


def run_checks():
    """
    Runs all cloud security baseline checks.
    Each rule returns a finding dictionary.
    """
    findings = []

    # S3 checks
    s3_buckets = load_json_file(S3_DATA_FILE)
    for bucket in s3_buckets:
        findings.append(check_s3_security_baseline(bucket))

    # EC2 Security Group checks
    security_groups = load_json_file(SECURITY_GROUP_DATA_FILE)
    for security_group in security_groups:
        findings.append(check_security_group_ssh_baseline(security_group))

    # IAM checks
    iam_users = load_json_file(IAM_DATA_FILE)
    for user in iam_users:
        findings.append(check_iam_user_baseline(user))

    # RDS checks
    rds_databases = load_json_file(RDS_DATA_FILE)
    for database in rds_databases:
        findings.append(check_rds_database_baseline(database))

    # CloudTrail checks
    cloudtrail_trails = load_json_file(CLOUDTRAIL_DATA_FILE)
    for trail in cloudtrail_trails:
        findings.append(check_cloudtrail_baseline(trail))

    # API Gateway / CloudFront checks
    public_endpoints = load_json_file(PUBLIC_ENDPOINT_DATA_FILE)
    for endpoint in public_endpoints:
        findings.append(check_public_endpoint_baseline(endpoint))

    # Lambda / Serverless checks
    lambda_functions = load_json_file(LAMBDA_DATA_FILE)
    for function in lambda_functions:
        findings.append(check_lambda_role_baseline(function))

    return findings


def prepare_website_alerts(findings):
    """
    Converts raw rule findings into website-ready alert variables.

    Only Warning and Danger findings are sent to the website.
    Safe findings are excluded because the alert dashboard should focus
    only on resources that need attention.
    """
    website_alerts = []

    for finding in findings:
        if finding["severity"] == "NONE":
            continue

        alert = {
            "alert_id": f"{finding['resource_name']}-{finding['severity'].lower()}",
            "generated_at": datetime.now().isoformat(),

            # Basic display information
            "team": finding["team"],
            "area": finding["area"],
            "resource_name": finding["resource_name"],
            "resource_type": finding["resource_type"],

            # Alert classification
            "status": finding["status"],
            "severity": finding["severity"],
            "finding_type": finding["finding_type"],

            # Manager-level view
            "manager_view": {
                "title": finding.get(
                    "manager_title",
                    f"{finding['finding_type']} alert for {finding['resource_name']}"
                ),
                "situation": finding["reason"],
                "business_risk": finding["risk"],
                "recommended_action": finding["manager_recommendation"]
            },

            # Technician-level view
            "technician_view": {
                "resource_id": finding["resource_id"],
                "rule": finding["rule"],
                "technical_reason": finding["reason"],
                "technical_fix": finding["technician_recommendation"]
            }
        }

        website_alerts.append(alert)

    return website_alerts


def scan_cloud_configurations():
    """
    Main scanner function.

    This function is used by:
    - main.py for testing
    - security_monitor.py for continuous monitoring
    - security_backend.py if needed later

    Returns:
    website-ready Warning and Danger alerts.
    """
    findings = run_checks()
    website_alerts = prepare_website_alerts(findings)
    return website_alerts


def print_website_alerts(website_alerts):
    """
    Prints prepared website alert variables for testing.
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