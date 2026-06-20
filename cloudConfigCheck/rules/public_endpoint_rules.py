def check_public_endpoint_baseline(endpoint):
    """
    Checks whether a public API Gateway or CloudFront endpoint meets the basic security baseline.

    Baseline rules:
    1. Public endpoints should use HTTPS.
    2. Public endpoints should have logging enabled.

    Case meaning:
    - safe: HTTPS and logging are enabled
    - warning: HTTPS is enabled, but logging is disabled
    - danger: HTTPS is disabled
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
            "rule": "Public customer/marketing endpoints should use HTTPS and logging",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",
            "reason": "The public endpoint does not enforce HTTPS.",
            "risk": "Data sent between users and the public endpoint may not be properly protected in transit.",

            "manager_recommendation": (
                "Urgent action is needed. A public manufacturing-related endpoint may allow insecure traffic. "
                "The manager should ask the cloud or IT team to enforce HTTPS immediately."
            ),

            "technician_recommendation": (
                "For CloudFront, configure the distribution to redirect HTTP to HTTPS and attach a valid TLS certificate. "
                "For API Gateway, ensure the endpoint uses HTTPS and review custom domain TLS settings. "
                "Enable access logging so requests can be monitored and investigated."
            )
        }

    if logging_missing:
        return {
            "resource_id": endpoint["resource_id"],
            "resource_name": endpoint["resource_name"],
            "resource_type": endpoint["resource_type"],
            "team": endpoint["team"],
            "case_type": endpoint["case_type"],
            "area": "API Gateway / CloudFront",
            "rule": "Public customer/marketing endpoints should use HTTPS and logging",
            "status": "FLAGGED",
            "severity": "MEDIUM",
            "finding_type": "Warning",
            "reason": "The public endpoint uses HTTPS, but logging is disabled.",
            "risk": "Traffic is protected in transit, but suspicious or unexpected access may be harder to investigate.",

            "manager_recommendation": (
                "This public endpoint uses secure HTTPS, but activity logging is missing. "
                "The manager should ask the cloud or IT team to enable logging so public access can be monitored."
            ),

            "technician_recommendation": (
                "Enable access logging for the public endpoint. For CloudFront, enable standard logs or real-time logs. "
                "For API Gateway, enable access logs and execution logs where appropriate. Store logs in a protected location."
            )
        }

    return {
        "resource_id": endpoint["resource_id"],
        "resource_name": endpoint["resource_name"],
        "resource_type": endpoint["resource_type"],
        "team": endpoint["team"],
        "case_type": endpoint["case_type"],
        "area": "API Gateway / CloudFront",
        "rule": "Public customer/marketing endpoints should use HTTPS and logging",
        "status": "PASSED",
        "severity": "NONE",
        "finding_type": "Safe",
        "reason": "The public endpoint uses HTTPS and logging is enabled.",
        "risk": "No public endpoint baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This public endpoint currently meets the expected security baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring HTTPS enforcement, certificates, and access logging."
        )
    }