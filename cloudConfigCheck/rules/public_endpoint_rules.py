def check_public_endpoint_baseline(endpoint):
    """
    Checks whether a public API Gateway / CloudFront endpoint meets the security baseline.

    Baseline rules:
    1. Public endpoints must enforce HTTPS.
    2. Public endpoints should have logging enabled.

    Case meaning:
    - safe: HTTPS enforced and logging enabled
    - warning: HTTPS enforced but logging disabled
    - danger: HTTPS not enforced
    """

    https_missing = endpoint["https_enabled"] is False
    logging_missing = endpoint["logging_enabled"] is False

    if https_missing:
        return {
            "resource_id": endpoint["resource_id"],
            "resource_name": endpoint["resource_name"],
            "resource_type": endpoint["resource_type"],
            "team": endpoint["team"],
            "case_type": endpoint["case_type"],
            "area": "API Gateway / CloudFront",
            "rule": "Public endpoints must enforce HTTPS and have logging enabled",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",

            "manager_title": "Public endpoint does not enforce HTTPS",
            "manager_aws_part": "Public website or API security settings",

            "reason": "A public-facing website or API endpoint does not enforce HTTPS.",
            "risk": "Data sent between users and the public endpoint may not be properly protected in transit.",

            "manager_recommendation": (
                "Ask the IT or cloud team to immediately enforce HTTPS for this public endpoint. "
                "This helps protect data moving between users, applications, and the company system."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to CloudFront or API Gateway, depending on the resource type shown above.",
                "Select the distribution or API shown in the resource ID.",
                "Check the HTTPS, viewer protocol, or stage security settings.",
                "Change the setting so HTTP traffic is redirected to HTTPS or HTTPS-only access is enforced.",
                "Attach or verify a valid TLS certificate.",
                "Save the change and test that public traffic cannot use insecure HTTP."
            ]
        }

    if logging_missing:
        return {
            "resource_id": endpoint["resource_id"],
            "resource_name": endpoint["resource_name"],
            "resource_type": endpoint["resource_type"],
            "team": endpoint["team"],
            "case_type": endpoint["case_type"],
            "area": "API Gateway / CloudFront",
            "rule": "Public endpoints must enforce HTTPS and have logging enabled",
            "status": "FLAGGED",
            "severity": "MEDIUM",
            "finding_type": "Warning",

            "manager_title": "Public endpoint logging is missing",
            "manager_aws_part": "Public website or API logging settings",

            "reason": "The public endpoint uses HTTPS, but activity logging is disabled.",
            "risk": "Suspicious or unexpected access may be harder to investigate because activity is not being recorded.",

            "manager_recommendation": (
                "Ask the IT or cloud team to enable logging for this public endpoint. "
                "This allows the company to monitor public access and investigate unusual activity."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to API Gateway or CloudFront, depending on the resource type shown above.",
                "Select the API or distribution shown in the resource ID.",
                "Go to logging, monitoring, stage settings, or distribution logging settings.",
                "Enable access logging.",
                "Send logs to an approved logging destination such as CloudWatch Logs or S3.",
                "Save the change and confirm that logs are generated after requests are made."
            ]
        }

    return {
        "resource_id": endpoint["resource_id"],
        "resource_name": endpoint["resource_name"],
        "resource_type": endpoint["resource_type"],
        "team": endpoint["team"],
        "case_type": endpoint["case_type"],
        "area": "API Gateway / CloudFront",
        "rule": "Public endpoints must enforce HTTPS and have logging enabled",
        "status": "PASSED",
        "severity": "NONE",
        "finding_type": "Safe",

        "manager_title": "Public endpoint is properly protected",
        "manager_aws_part": "Public website or API security settings",

        "reason": "The public endpoint enforces HTTPS and has logging enabled.",
        "risk": "No public endpoint baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This public endpoint currently meets the expected security baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring HTTPS enforcement and access logging."
        )
    }