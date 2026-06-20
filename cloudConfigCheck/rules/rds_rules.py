def check_rds_database_baseline(database):
    """
    Checks whether an RDS database meets the basic professional security baseline.

    Baseline rules:
    1. RDS databases must not be publicly accessible.
    2. RDS databases should be encrypted.
    3. RDS backups should be enabled.

    Case meaning:
    - safe: database is private, encrypted, and backed up
    - warning: database is private, but missing encryption or backups
    - danger: database is publicly accessible
    """

    is_public = database["publicly_accessible"] is True
    encryption_missing = database["encryption_enabled"] is False
    backup_missing = database["backup_enabled"] is False

    if is_public:
        return {
            "resource_id": database["resource_id"],
            "resource_name": database["resource_name"],
            "resource_type": database["resource_type"],
            "team": database["team"],
            "case_type": database["case_type"],
            "area": "RDS",
            "rule": "Project/manufacturing databases must not be public",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",
            "reason": "The RDS database is publicly accessible from the internet.",
            "risk": "Internal manufacturing database records could be exposed or targeted from outside the company.",

            "manager_recommendation": (
                "Urgent action is needed. A manufacturing database may be reachable from the internet. "
                "The manager should ask the cloud or IT team to make the database private immediately."
            ),

            "technician_recommendation": (
                "In AWS RDS, disable Publicly Accessible for this database. Place the database in private subnets, "
                "restrict its security group to only approved application servers, enable encryption, and enable automated backups."
            )
        }

    if encryption_missing or backup_missing:
        missing_items = []

        if encryption_missing:
            missing_items.append("encryption")

        if backup_missing:
            missing_items.append("automated backups")

        return {
            "resource_id": database["resource_id"],
            "resource_name": database["resource_name"],
            "resource_type": database["resource_type"],
            "team": database["team"],
            "case_type": database["case_type"],
            "area": "RDS",
            "rule": "RDS databases should meet the professional security baseline",
            "status": "FLAGGED",
            "severity": "MEDIUM",
            "finding_type": "Warning",
            "reason": f"The RDS database is private, but missing: {', '.join(missing_items)}.",
            "risk": "The database is not publicly exposed, but stored manufacturing data is not fully protected according to the expected baseline.",

            "manager_recommendation": (
                "This manufacturing database is not publicly exposed, but it is still below the expected security baseline. "
                "The manager should ask the cloud or IT team to review database protection settings."
            ),

            "technician_recommendation": (
                "In AWS RDS, enable storage encryption if supported by the database setup. Ensure automated backups are enabled "
                "with an appropriate retention period. Confirm that the database remains in private subnets and is not publicly accessible."
            )
        }

    return {
        "resource_id": database["resource_id"],
        "resource_name": database["resource_name"],
        "resource_type": database["resource_type"],
        "team": database["team"],
        "case_type": database["case_type"],
        "area": "RDS",
        "rule": "RDS databases should meet the professional security baseline",
        "status": "PASSED",
        "severity": "NONE",
        "finding_type": "Safe",
        "reason": "The RDS database is private, encrypted, and has backups enabled.",
        "risk": "No RDS baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This database currently meets the expected RDS security baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring public accessibility, encryption, backups, and database security group rules."
        )
    }