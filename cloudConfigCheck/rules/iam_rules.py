def check_iam_user_baseline(user):
    """
    Checks whether an IAM user meets the basic identity security baseline.

    Baseline rules:
    1. Non-admin users must not have AdministratorAccess.
    2. Old or unused access keys should be flagged.

    Case meaning:
    - safe: user follows least privilege and access key is recent
    - warning: user has no admin access, but access key is old or unused
    - danger: non-admin user has AdministratorAccess
    """

    has_admin_access = "AdministratorAccess" in user["attached_policies"]

    old_access_key = user["access_key_age_days"] > 90
    unused_access_key = user["access_key_last_used_days_ago"] > 90

    if has_admin_access and user["is_admin_user"] is False:
        return {
            "resource_id": user["resource_id"],
            "resource_name": user["resource_name"],
            "resource_type": user["resource_type"],
            "team": user["team"],
            "case_type": user["case_type"],
            "area": "IAM",
            "rule": "Non-admin users must not have AdministratorAccess",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",
            "reason": "A non-admin IAM user has AdministratorAccess.",
            "risk": "This user may be able to change, delete, or access critical AWS resources beyond their job responsibility.",

            "manager_recommendation": (
                "Urgent action is needed. A manufacturing user has administrator-level cloud access. "
                "The manager should ask the cloud or IT team to review and reduce this user's permissions immediately."
            ),

            "technician_recommendation": (
                "In AWS IAM, remove the AdministratorAccess policy from this user. Replace it with a least-privilege "
                "policy that only allows the actions required for the user's manufacturing role. Review whether this "
                "user should be converted to a role-based access model instead of using long-term user credentials."
            )
        }

    if old_access_key or unused_access_key:
        return {
            "resource_id": user["resource_id"],
            "resource_name": user["resource_name"],
            "resource_type": user["resource_type"],
            "team": user["team"],
            "case_type": user["case_type"],
            "area": "IAM",
            "rule": "Old or unused access keys should be flagged",
            "status": "FLAGGED",
            "severity": "MEDIUM",
            "finding_type": "Warning",
            "reason": "The IAM user's access key is old or has not been used recently.",
            "risk": "Old or unused access keys increase the risk of forgotten credentials being exposed or misused.",

            "manager_recommendation": (
                "This user does not have administrator access, but the access key is old or unused. "
                "The manager should ask the cloud or IT team to rotate or remove unnecessary access keys."
            ),

            "technician_recommendation": (
                "In AWS IAM, review the user's access keys. Rotate keys older than 90 days and deactivate or delete "
                "keys that are no longer required. Confirm that applications using the key are updated before removal."
            )
        }

    return {
        "resource_id": user["resource_id"],
        "resource_name": user["resource_name"],
        "resource_type": user["resource_type"],
        "team": user["team"],
        "case_type": user["case_type"],
        "area": "IAM",
        "rule": "IAM users must follow least privilege and access key hygiene",
        "status": "PASSED",
        "severity": "NONE",
        "finding_type": "Safe",
        "reason": "The IAM user does not have administrator access and the access key is recent.",
        "risk": "No IAM baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This IAM user currently follows the expected identity security baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring permissions and access key age."
        )
    }