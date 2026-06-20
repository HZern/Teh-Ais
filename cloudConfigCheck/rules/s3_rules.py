def check_s3_security_baseline(bucket):
    """
    Checks whether an S3 bucket meets the basic professional security baseline.

    Baseline rules:
    1. The S3 bucket must not be publicly accessible.
    2. The S3 bucket must have encryption enabled.

    Recommendation design:
    - manager_recommendation: simple business-level explanation
    - technician_recommendation: specific technical fix
    """

    is_public = (
        bucket["public_access_blocked"] is False
        or bucket["bucket_policy_public"] is True
        or bucket["acl_public"] is True
    )

    encryption_missing = bucket["encryption_enabled"] is False

    # Danger case:
    # The bucket may be publicly accessible.
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
            "reason": "The S3 bucket may be publicly accessible.",
            "risk": "Sensitive manufacturing documents, machine output files, or production records could be exposed online.",

            "manager_recommendation": (
                "Urgent action is needed. This manufacturing storage bucket may be publicly accessible, "
                "which could expose internal production files or machine data. The manager should notify "
                "the cloud or IT team to restrict public access immediately."
            ),

            "technician_recommendation": (
                "In AWS S3, enable Block Public Access for this bucket. Review and remove any bucket policy "
                "that allows public access, especially policies with Principal set to '*'. Disable public ACLs, "
                "confirm the bucket is not internet-accessible, and enable default server-side encryption."
            )
        }

    # Warning case:
    # The bucket is private, but still does not fully meet the baseline.
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
            "reason": "The S3 bucket is not publicly accessible, but encryption is disabled.",
            "risk": "The bucket is not directly exposed, but stored manufacturing files are not protected according to the professional baseline.",

            "manager_recommendation": (
                "This bucket is not publicly exposed, but it is still below the expected security baseline "
                "because encryption is disabled. The manager should ask the cloud or IT team to enable "
                "encryption to better protect manufacturing records."
            ),

            "technician_recommendation": (
                "In AWS S3, enable default server-side encryption for this bucket. Use SSE-S3 or SSE-KMS "
                "depending on company policy. After enabling encryption, verify that future uploaded objects "
                "are encrypted by default."
            )
        }

    # Safe case:
    # The bucket is private and encrypted.
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
        "reason": "The S3 bucket is private and encrypted.",
        "risk": "No S3 baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This bucket currently meets the expected S3 security baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring the bucket configuration and keep public access blocked and encryption enabled."
        )
    }