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

            "manager_title": "Serverless function has excessive permissions",
            "manager_aws_part": "Lambda function role permission settings",

            "reason": "A serverless function has administrator-level cloud permissions.",
            "risk": "If this small function is misused or compromised, it may be able to access or change critical AWS resources.",

            "manager_recommendation": (
                "Ask the cloud or IT team to immediately reduce this function's permissions. "
                "The function should only have the access required to perform its specific task."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to Lambda.",
                "Search for and select the Lambda function shown in the resource ID.",
                "Open the Configuration tab.",
                "Go to Permissions.",
                "Click the execution role linked to this Lambda function.",
                "In IAM, review the policies attached to the execution role.",
                "Remove AdministratorAccess or any unnecessary broad policies.",
                "Create or attach a least-privilege policy that only allows the exact AWS actions and resources required by the function.",
                "Save the permission changes and test that the Lambda function still works correctly."
            ]
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

            "manager_title": "Serverless permissions need review",
            "manager_aws_part": "Lambda function role permission settings",

            "reason": "A serverless function has broader cloud permissions than it likely needs.",
            "risk": "The function does not have full administrator access, but its permissions may still be wider than necessary.",

            "manager_recommendation": (
                "Ask the cloud or IT team to review whether this function really needs these permissions. "
                "Unnecessary broad permissions should be replaced with more specific access."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to Lambda.",
                "Search for and select the Lambda function shown in the resource ID.",
                "Open the Configuration tab.",
                "Go to Permissions.",
                "Click the execution role linked to this Lambda function.",
                "In IAM, review the policies attached to the execution role.",
                "Look for broad policies such as AmazonS3FullAccess or wildcard permissions.",
                "Replace broad permissions with a narrower custom policy, such as read-only or write-only access to the specific S3 bucket required by the function.",
                "Save the permission changes and test that the Lambda function still works correctly."
            ]
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

        "manager_title": "Serverless permissions are properly restricted",
        "manager_aws_part": "Lambda function role permission settings",

        "reason": "The serverless function role follows least privilege.",
        "risk": "No Lambda permission baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This Lambda function role currently follows the expected permission baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring Lambda execution roles and avoid broad permissions."
        )
    }