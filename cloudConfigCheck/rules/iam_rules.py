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

            "manager_title": "User has excessive cloud permissions",
            "manager_aws_part": "IAM user permission settings",

            "reason": "A user account has administrator-level cloud access even though it is not meant to be an admin user.",
            "risk": "This user may be able to change, delete, or access critical AWS resources beyond their job responsibility.",

            "manager_recommendation": (
                "Ask the cloud or IT team to immediately review and reduce this user's permissions. "
                "The user should only have the access required for their role."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to IAM.",
                "In the left menu, open Users.",
                "Search for and select the IAM user shown in the resource ID.",
                "Go to the Permissions tab.",
                "Remove the AdministratorAccess policy from this user.",
                "Attach a least-privilege policy that only allows the actions required for this user's role.",
                "Review whether this user should be replaced with role-based access instead of long-term IAM user credentials."
            ]
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

            "manager_title": "Access key needs review",
            "manager_aws_part": "IAM access key settings",

            "reason": "A user's access key is old or has not been used recently.",
            "risk": "Old or unused access keys increase the risk of forgotten credentials being exposed or misused.",

            "manager_recommendation": (
                "Ask the cloud or IT team to review this access key. "
                "If it is still needed, rotate it. If it is no longer needed, remove it."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to IAM.",
                "In the left menu, open Users.",
                "Search for and select the IAM user shown in the resource ID.",
                "Go to the Security credentials tab.",
                "Review the user's access keys.",
                "Rotate access keys older than 90 days if they are still required.",
                "Deactivate and delete access keys that are no longer required.",
                "Before deleting a key, confirm that any applications using the key have been updated."
            ]
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

        "manager_title": "User permissions are properly restricted",
        "manager_aws_part": "IAM user permission and access key settings",

        "reason": "The IAM user does not have administrator access and the access key is recent.",
        "risk": "No IAM baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This IAM user currently follows the expected identity security baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring permissions and access key age."
        )
    }