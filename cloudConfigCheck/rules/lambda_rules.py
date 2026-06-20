def check_lambda_role_baseline(function):
    """
    Checks whether a Lambda function role follows the least privilege baseline.

    Baseline rule:
    Lambda function roles should follow least privilege.

    Case meaning:
    - safe: role only has required limited permissions
    - warning: role has broad permissions, but not full administrator access
    - danger: role has AdministratorAccess or excessive cloud access
    """

    has_admin_access = function["has_admin_access"] is True
    has_wildcard_permissions = function["has_wildcard_permissions"] is True

    if has_admin_access:
        return {
            "resource_id": function["resource_id"],
            "resource_name": function["resource_name"],
            "resource_type": function["resource_type"],
            "team": function["team"],
            "case_type": function["case_type"],
            "area": "Lambda / Serverless",
            "rule": "Function roles should follow least privilege",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",
            "reason": "The Lambda function role has administrator-level permissions.",
            "risk": "If this small function is misused or compromised, it may be able to access or change critical AWS resources.",

            "manager_recommendation": (
                "Urgent action is needed. A manufacturing serverless function has excessive cloud access. "
                "The manager should ask the cloud or IT team to reduce the function role permissions immediately."
            ),

            "technician_recommendation": (
                "In AWS IAM, review the execution role attached to this Lambda function. Remove AdministratorAccess "
                "or any unnecessary broad policies. Replace them with a least-privilege custom policy that only allows "
                "the exact AWS actions and resources required by the function."
            )
        }

    if has_wildcard_permissions:
        return {
            "resource_id": function["resource_id"],
            "resource_name": function["resource_name"],
            "resource_type": function["resource_type"],
            "team": function["team"],
            "case_type": function["case_type"],
            "area": "Lambda / Serverless",
            "rule": "Function roles should follow least privilege",
            "status": "FLAGGED",
            "severity": "MEDIUM",
            "finding_type": "Warning",
            "reason": "The Lambda function role has broader permissions than needed.",
            "risk": "The function does not have full administrator access, but its permissions may still be wider than necessary.",

            "manager_recommendation": (
                "This serverless function is not fully dangerous, but its cloud permissions may be too broad. "
                "The manager should ask the cloud or IT team to review whether the function really needs these permissions."
            ),

            "technician_recommendation": (
                "Review the Lambda execution role and attached policies. Replace broad managed policies such as "
                "AmazonS3FullAccess with narrower custom policies, for example read or write access only to the specific "
                "S3 bucket required by the function."
            )
        }

    return {
        "resource_id": function["resource_id"],
        "resource_name": function["resource_name"],
        "resource_type": function["resource_type"],
        "team": function["team"],
        "case_type": function["case_type"],
        "area": "Lambda / Serverless",
        "rule": "Function roles should follow least privilege",
        "status": "PASSED",
        "severity": "NONE",
        "finding_type": "Safe",
        "reason": "The Lambda function role follows least privilege.",
        "risk": "No Lambda permission baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This Lambda function role currently follows the expected permission baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring Lambda execution roles and avoid broad permissions."
        )
    }