def check_cloudtrail_baseline(trail):
    """
    Checks whether CloudTrail meets the basic audit logging baseline.

    Baseline rules:
    1. CloudTrail logging must be enabled.
    2. Multi-region logging should be enabled.
    3. Log file validation should be enabled.

    Case meaning:
    - safe: logging is enabled with stronger audit settings
    - warning: logging is enabled, but audit settings are incomplete
    - danger: logging is disabled
    """

    logging_disabled = trail["logging_enabled"] is False
    multi_region_missing = trail["multi_region_enabled"] is False
    validation_missing = trail["log_file_validation_enabled"] is False

    if logging_disabled:
        return {
            "resource_id": trail["resource_id"],
            "resource_name": trail["resource_name"],
            "resource_type": trail["resource_type"],
            "team": trail["team"],
            "case_type": trail["case_type"],
            "area": "CloudTrail",
            "rule": "CloudTrail logging must be enabled",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",
            "reason": "CloudTrail logging is disabled.",
            "risk": "The organisation may not have a reliable audit trail of who changed AWS resources and when changes occurred.",

            "manager_recommendation": (
                "Urgent action is needed. Cloud activity for manufacturing resources may not be properly recorded. "
                "The manager should ask the cloud or IT team to enable CloudTrail logging immediately so changes can be audited."
            ),

            "technician_recommendation": (
                "In AWS CloudTrail, enable logging for this trail. Ensure the trail records management events, stores logs in a protected S3 bucket, "
                "and enable multi-region logging and log file validation where required by company policy."
            )
        }

    if multi_region_missing or validation_missing:
        missing_items = []

        if multi_region_missing:
            missing_items.append("multi-region logging")

        if validation_missing:
            missing_items.append("log file validation")

        return {
            "resource_id": trail["resource_id"],
            "resource_name": trail["resource_name"],
            "resource_type": trail["resource_type"],
            "team": trail["team"],
            "case_type": trail["case_type"],
            "area": "CloudTrail",
            "rule": "CloudTrail should meet the professional audit logging baseline",
            "status": "FLAGGED",
            "severity": "MEDIUM",
            "finding_type": "Warning",
            "reason": f"CloudTrail logging is enabled, but missing: {', '.join(missing_items)}.",
            "risk": "AWS activity is being logged, but the audit setup may not be complete enough for stronger monitoring and investigation.",

            "manager_recommendation": (
                "Cloud activity is being recorded, but the audit setup is incomplete. The manager should ask the cloud or IT team "
                "to improve CloudTrail settings so manufacturing cloud changes can be monitored more reliably."
            ),

            "technician_recommendation": (
                "Review the CloudTrail configuration. Enable multi-region logging if the AWS account uses or may use multiple regions. "
                "Enable log file validation to help verify that logs have not been changed after delivery."
            )
        }

    return {
        "resource_id": trail["resource_id"],
        "resource_name": trail["resource_name"],
        "resource_type": trail["resource_type"],
        "team": trail["team"],
        "case_type": trail["case_type"],
        "area": "CloudTrail",
        "rule": "CloudTrail should meet the professional audit logging baseline",
        "status": "PASSED",
        "severity": "NONE",
        "finding_type": "Safe",
        "reason": "CloudTrail logging is enabled with multi-region logging and log file validation.",
        "risk": "No CloudTrail audit logging issue detected.",

        "manager_recommendation": (
            "No management action is needed. CloudTrail currently meets the expected audit logging baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring CloudTrail logging, log file validation, and log storage protection."
        )
    }