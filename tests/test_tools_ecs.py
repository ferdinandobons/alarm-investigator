"""Tests for ECS tools."""

from unittest.mock import MagicMock

from alarm_investigator.tools.ecs import DescribeECSServiceTool


class TestDescribeECSServiceTool:
    """Tests for DescribeECSServiceTool."""

    def test_tool_has_correct_spec(self):
        """Test tool has correct Bedrock spec."""
        tool = DescribeECSServiceTool(ecs_client=MagicMock())
        spec = tool.to_bedrock_spec()

        assert spec["toolSpec"]["name"] == "describe_ecs_service"
        assert "cluster" in spec["toolSpec"]["inputSchema"]["json"]["properties"]
        assert "service" in spec["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_execute_returns_service_info(self):
        """Test executing tool returns service information."""
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {
            "services": [
                {
                    "serviceName": "my-service",
                    "serviceArn": (
                        "arn:aws:ecs:us-east-1:123456789012:service/my-cluster/my-service"
                    ),
                    "status": "ACTIVE",
                    "desiredCount": 3,
                    "runningCount": 3,
                    "pendingCount": 0,
                    "launchType": "FARGATE",
                    "deployments": [
                        {
                            "id": "ecs-svc/123",
                            "status": "PRIMARY",
                            "desiredCount": 3,
                            "runningCount": 3,
                            "rolloutState": "COMPLETED",
                        }
                    ],
                }
            ]
        }

        tool = DescribeECSServiceTool(ecs_client=mock_client)
        result = tool.execute(cluster="my-cluster", service="my-service")

        assert result["status"] == "success"
        assert result["service"]["name"] == "my-service"
        assert result["service"]["status"] == "ACTIVE"
        assert result["service"]["desired_count"] == 3
        assert result["service"]["running_count"] == 3
        assert result["service"]["launch_type"] == "FARGATE"

    def test_execute_handles_not_found(self):
        """Test tool handles service not found."""
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {
            "services": [],
            "failures": [{"reason": "MISSING"}],
        }

        tool = DescribeECSServiceTool(ecs_client=mock_client)
        result = tool.execute(cluster="my-cluster", service="nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_execute_handles_api_error(self):
        """Test tool handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.describe_services.side_effect = Exception("Access Denied")

        tool = DescribeECSServiceTool(ecs_client=mock_client)
        result = tool.execute(cluster="my-cluster", service="my-service")

        assert result["status"] == "error"
        assert "Access Denied" in result["error"]
