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
            "rule": "Databases must not be publicly accessible",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",

            "manager_title": "Database may be publicly reachable",
            "manager_aws_part": "RDS database public access settings",

            "reason": "A cloud database may be reachable from the public internet.",
            "risk": "Internal database records could be exposed or targeted by people outside the company.",

            "manager_recommendation": (
                "Ask the IT or cloud team to immediately make this database private. "
                "The database should only be reachable by approved internal applications or systems."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to RDS.",
                "In the left menu, open Databases.",
                "Select the database shown in the resource ID.",
                "Check the Connectivity & security settings.",
                "Disable the Publicly Accessible setting for this database.",
                "Place the database in private subnets.",
                "Restrict the database security group so only approved application servers can connect.",
                "Enable storage encryption if supported by the database setup.",
                "Enable automated backups with an appropriate retention period.",
                "Save the changes and confirm the database is no longer reachable from the public internet."
            ]
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

            "manager_title": "Database protection needs review",
            "manager_aws_part": "RDS database protection settings",

            "reason": f"The database is private, but missing: {', '.join(missing_items)}.",
            "risk": "The database is not publicly exposed, but stored company data is not fully protected according to the expected baseline.",

            "manager_recommendation": (
                "Ask the IT or cloud team to review this database protection setup. "
                "The database is not publicly exposed, but encryption and backup settings should meet the company security baseline."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to RDS.",
                "In the left menu, open Databases.",
                "Select the database shown in the resource ID.",
                "Check whether storage encryption is enabled.",
                "If encryption is missing, enable storage encryption if supported by the database setup.",
                "Check whether automated backups are enabled.",
                "If backups are missing, enable automated backups with an appropriate retention period.",
                "Confirm that the database remains in private subnets.",
                "Confirm that Publicly Accessible is disabled."
            ]
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

        "manager_title": "Database is properly protected",
        "manager_aws_part": "RDS database protection settings",

        "reason": "The database is private, encrypted, and has backups enabled.",
        "risk": "No RDS baseline issue detected.",

        "manager_recommendation": (
            "No management action is needed. This database currently meets the expected RDS security baseline."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring public accessibility, encryption, backups, and database security group rules."
        )
    }