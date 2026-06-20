def check_security_group_ssh_baseline(security_group):
    """
    Checks whether an EC2 Security Group meets the SSH access baseline.

    Baseline rule:
    SSH on port 22 must not be open to 0.0.0.0/0.

    Case meaning:
    - safe: SSH is not open
    - warning: SSH is restricted to a specific IP, but should still be reviewed
    - danger: SSH is open to the entire internet
    """

    inbound_rules = security_group["inbound_rules"]

    ssh_open_to_internet = False
    ssh_restricted = False

    for rule in inbound_rules:
        is_ssh = rule["protocol"] == "tcp" and rule["port"] == 22

        if is_ssh and rule["source"] == "0.0.0.0/0":
            ssh_open_to_internet = True

        elif is_ssh and rule["source"] != "0.0.0.0/0":
            ssh_restricted = True

    if ssh_open_to_internet:
        return {
            "resource_id": security_group["resource_id"],
            "resource_name": security_group["resource_name"],
            "resource_type": security_group["resource_type"],
            "team": security_group["team"],
            "case_type": security_group["case_type"],
            "area": "EC2 / Security Groups",
            "rule": "SSH must not be open to 0.0.0.0/0",
            "status": "FAILED",
            "severity": "HIGH",
            "finding_type": "Danger",

            "manager_title": "Server admin access may be exposed online",
            "manager_aws_part": "Server firewall access settings",

            "reason": "A server may allow administrator access from the public internet.",
            "risk": "People outside the company may be able to attempt remote access to this server, increasing the risk of unauthorised control.",

            "manager_recommendation": (
                "Ask the IT or cloud team to immediately block public admin access to this server. "
                "Admin access should only be allowed through approved secure methods, such as a company VPN, "
                "bastion host, or controlled access system."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to EC2.",
                "In the left menu, open Security Groups.",
                "Select the security group shown in the resource ID.",
                "Go to Inbound rules.",
                "Find the rule that allows TCP port 22 from 0.0.0.0/0.",
                "Delete this public SSH rule.",
                "If SSH is still required, add a new rule that only allows access from an approved company VPN IP range or bastion host.",
                "Consider using AWS Systems Manager Session Manager instead of public SSH access."
            ]
        }

    if ssh_restricted:
        return {
            "resource_id": security_group["resource_id"],
            "resource_name": security_group["resource_name"],
            "resource_type": security_group["resource_type"],
            "team": security_group["team"],
            "case_type": security_group["case_type"],
            "area": "EC2 / Security Groups",
            "rule": "SSH must not be open to 0.0.0.0/0",
            "status": "FLAGGED",
            "severity": "MEDIUM",
            "finding_type": "Warning",

            "manager_title": "Server access needs review",
            "manager_aws_part": "Server firewall access settings",

            "reason": "Server administration access is allowed only from a restricted network, but it should still be reviewed.",
            "risk": "The server is not open to everyone, but admin access should be checked to confirm it is approved, still needed, and limited to trusted networks.",

            "manager_recommendation": (
                "Ask the IT or cloud team to confirm whether this server admin access is still required. "
                "If it is not needed, remove it. If it is needed, ensure it is limited to an approved company network."
            ),

            "technician_recommendation": [
                "Open AWS Console and go to EC2.",
                "In the left menu, open Security Groups.",
                "Select the security group shown in the resource ID.",
                "Go to Inbound rules.",
                "Find the SSH rule using TCP port 22.",
                "Check whether the source IP range belongs to an approved company VPN or bastion host.",
                "If the SSH rule is not required anymore, delete it.",
                "If it is still required, document why it is needed and keep the source limited to trusted networks only."
            ]
        }

    return {
        "resource_id": security_group["resource_id"],
        "resource_name": security_group["resource_name"],
        "resource_type": security_group["resource_type"],
        "team": security_group["team"],
        "case_type": security_group["case_type"],
        "area": "EC2 / Security Groups",
        "rule": "SSH must not be open to 0.0.0.0/0",
        "status": "PASSED",
        "severity": "NONE",
        "finding_type": "Safe",

        "manager_title": "Server access is properly restricted",
        "manager_aws_part": "Server firewall access settings",

        "reason": "SSH is not open in this security group.",
        "risk": "No SSH exposure detected.",

        "manager_recommendation": (
            "No management action is needed. This server firewall configuration does not expose SSH access."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring this security group and avoid opening SSH to the internet."
        )
    }