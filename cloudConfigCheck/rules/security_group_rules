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
            "reason": "SSH access is open to the entire internet.",
            "risk": "Attackers may attempt remote admin access to the manufacturing server.",

            "manager_recommendation": (
                "Urgent action is needed. The firewall rules protecting this manufacturing server "
                "allow SSH admin access from the internet. The manager should ask the cloud or IT team "
                "to restrict SSH access immediately."
            ),

            "technician_recommendation": (
                "In the EC2 Security Group inbound rules, remove the rule that allows TCP port 22 "
                "from 0.0.0.0/0. Restrict SSH access to an approved VPN IP range or bastion host, "
                "or use AWS Systems Manager Session Manager instead of public SSH."
            )
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
            "reason": "SSH access is restricted to a specific IP range, but still needs review.",
            "risk": "The server is not open to everyone, but admin access should be checked to confirm it is approved and still required.",

            "manager_recommendation": (
                "This server is not open to the whole internet, but SSH admin access is still enabled. "
                "The manager should confirm with the cloud or IT team that this access is approved and necessary."
            ),

            "technician_recommendation": (
                "Review the EC2 Security Group inbound SSH rule. Confirm that the source IP range belongs "
                "to an approved company VPN or bastion host. Remove the SSH rule if it is no longer needed."
            )
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
        "reason": "SSH is not open in this security group.",
        "risk": "No SSH exposure detected.",

        "manager_recommendation": (
            "No management action is needed. This security group does not expose SSH access."
        ),

        "technician_recommendation": (
            "No technical change is required. Continue monitoring this security group and avoid opening SSH to the internet."
        )
    }