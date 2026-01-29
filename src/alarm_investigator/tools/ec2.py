"""EC2 investigation tools."""

from alarm_investigator.tools.base import Tool


class DescribeEC2InstanceTool(Tool):
    """Tool to describe an EC2 instance."""

    name = "describe_ec2_instance"
    description = (
        "Get detailed information about an EC2 instance including its state, "
        "type, network configuration, and tags. Use this to understand the "
        "current state and configuration of an instance related to an alarm."
    )

    def __init__(self, ec2_client):
        self._client = ec2_client

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "instance_id": {
                    "type": "string",
                    "description": "The EC2 instance ID (e.g., i-1234567890abcdef0)",
                }
            },
            "required": ["instance_id"],
        }

    def execute(self, instance_id: str, **kwargs) -> dict:
        """Describe an EC2 instance."""
        try:
            response = self._client.describe_instances(InstanceIds=[instance_id])

            reservations = response.get("Reservations", [])
            if not reservations or not reservations[0].get("Instances"):
                return {"status": "error", "error": f"Instance {instance_id} not found"}

            instance = reservations[0]["Instances"][0]

            # Extract name from tags
            name = None
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
                    break

            return {
                "status": "success",
                "instance": {
                    "instance_id": instance["InstanceId"],
                    "instance_type": instance.get("InstanceType"),
                    "state": instance.get("State", {}).get("Name"),
                    "launch_time": str(instance.get("LaunchTime", "")),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "vpc_id": instance.get("VpcId"),
                    "subnet_id": instance.get("SubnetId"),
                    "name": name,
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])
                    },
                },
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
