"""Tests for EC2 tools."""

from unittest.mock import MagicMock

from alarm_investigator.tools.ec2 import DescribeEC2InstanceTool


class TestDescribeEC2InstanceTool:
    """Tests for DescribeEC2InstanceTool."""

    def test_tool_has_correct_spec(self):
        """Test tool has correct Bedrock spec."""
        tool = DescribeEC2InstanceTool(ec2_client=MagicMock())
        spec = tool.to_bedrock_spec()

        assert spec["toolSpec"]["name"] == "describe_ec2_instance"
        assert "instance_id" in spec["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_execute_returns_instance_info(self):
        """Test executing tool returns instance information."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "InstanceType": "t3.medium",
                            "State": {"Name": "running"},
                            "LaunchTime": "2026-01-01T00:00:00Z",
                            "PrivateIpAddress": "10.0.1.100",
                            "PublicIpAddress": "54.1.2.3",
                            "VpcId": "vpc-12345",
                            "SubnetId": "subnet-12345",
                            "Tags": [{"Key": "Name", "Value": "WebServer"}],
                        }
                    ]
                }
            ]
        }

        tool = DescribeEC2InstanceTool(ec2_client=mock_client)
        result = tool.execute(instance_id="i-1234567890abcdef0")

        assert result["status"] == "success"
        assert result["instance"]["instance_id"] == "i-1234567890abcdef0"
        assert result["instance"]["instance_type"] == "t3.medium"
        assert result["instance"]["state"] == "running"
        assert result["instance"]["name"] == "WebServer"

    def test_execute_handles_not_found(self):
        """Test tool handles instance not found."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {"Reservations": []}

        tool = DescribeEC2InstanceTool(ec2_client=mock_client)
        result = tool.execute(instance_id="i-nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_execute_handles_api_error(self):
        """Test tool handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.describe_instances.side_effect = Exception("Access Denied")

        tool = DescribeEC2InstanceTool(ec2_client=mock_client)
        result = tool.execute(instance_id="i-1234567890abcdef0")

        assert result["status"] == "error"
        assert "Access Denied" in result["error"]
