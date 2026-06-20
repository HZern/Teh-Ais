def check_s3_security_baseline(bucket):
    """
    Checks whether an S3 bucket meets the basic professional security baseline.

    Baseline rules:
    1. The S3 bucket must not be publicly accessible.
    2. The S3 bucket must have encryption enabled.
    """

    is_public = (
        bucket["public_access_blocked"] is False
        or bucket["bucket_policy_public"] is True
        or bucket["acl_public"] is True
    )

    encryption_missing = bucket["encryption_enabled"] is False

    if is_public:
        return {
            "resource_id": bucket["resource_id"],
            "resource_name": bucket["resource_name"],
            "resource_type": bucket["resource_type"],
            "team": bucket["team"],
            "case_type": bucket["case_type"],
            "area": "S3",
            "rule": "S3 buckets must meet the professional security baseline",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",

            "manager_title": "Cloud storage may be publicly accessible",
            "manager_aws_part": "S3 cloud storage access settings",

            "reason": "A cloud storage location may be accessible from the public internet.",
            "risk": "Internal files, documents, or operational records may be viewed by people outside the company.",

            "manager_recommendation": (
                "Ask the IT or cloud team to immediately block public access to this storage location "
                "and confirm that only approved users or systems can access it."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to S3.",
                "Search for and select the bucket shown in the resource ID.",
                "Go to the Permissions tab.",
                "Enable Block Public Access for this bucket.",
                "Review the bucket policy and remove any statement that allows public access, especially policies with Principal set to '*'.",
                "Review Object Ownership and ACL settings, and disable public ACL access.",
                "Confirm the bucket is no longer publicly accessible.",
                "Go to the Properties tab.",
                "Enable default server-side encryption using SSE-S3 or SSE-KMS, depending on company policy."
            ]
        }

    if encryption_missing:
        return {
            "resource_id": bucket["resource_id"],
            "resource_name": bucket["resource_name"],
            "resource_type": bucket["resource_type"],
            "team": bucket["team"],
            "case_type": bucket["case_type"],
            "area": "S3",
            "rule": "S3 buckets must meet the professional security baseline",
            "status": "FLAGGED",
            "severity": "MEDIUM",
            "finding_type": "Warning",

            "manager_title": "Cloud storage needs encryption",
            "manager_aws_part": "S3 cloud storage encryption settings",

            "reason": "This cloud storage location is not open to the public, but its files are not protected with encryption.",
            "risk": "If someone gains access to this storage location, stored files may be easier to read because encryption is not enabled.",

            "manager_recommendation": (
                "Ask the IT or cloud team to enable encryption for this storage location. "
                "This is not an emergency exposure, but it should be fixed to meet the company security baseline."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to S3.",
                "Search for and select the bucket shown in the resource ID.",
                "Go to the Properties tab.",
                "Find Default encryption.",
                "Enable default server-side encryption.",
                "Choose SSE-S3 or SSE-KMS depending on company policy.",
                "Save the encryption setting.",
                "Upload or check a test object to confirm future objects are encrypted by default."
            ]
        }

    return {
        "resource_id": bucket["resource_id"],
        "resource_name": bucket["resource_name"],
        "resource_type": bucket["resource_type"],
        "team": bucket["team"],
        "case_type": bucket["case_type"],
        "area": "S3",
        "rule": "S3 buckets must meet the professional security baseline",
        "status": "PASSED",
        "severity": "NONE",
        "finding_type": "Safe",

        "manager_title": "Cloud storage is properly protected",
        "manager_aws_part": "S3 cloud storage settings",

        "reason": "The cloud storage location is private and encrypted.",
        "risk": "No S3 baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This storage location currently meets the expected security baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring the bucket configuration and keep public access blocked and encryption enabled."
        )
    }