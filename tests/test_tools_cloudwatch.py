"""Tests for CloudWatch tools."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from alarm_investigator.tools.cloudwatch import GetMetricsTool


class TestGetMetricsTool:
    """Tests for GetMetricsTool."""

    def test_tool_has_correct_spec(self):
        """Test tool has correct Bedrock spec."""
        tool = GetMetricsTool(cloudwatch_client=MagicMock())
        spec = tool.to_bedrock_spec()

        assert spec["toolSpec"]["name"] == "get_cloudwatch_metrics"
        assert "namespace" in spec["toolSpec"]["inputSchema"]["json"]["properties"]
        assert "metric_name" in spec["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_execute_returns_metric_data(self):
        """Test executing tool returns metric data."""
        mock_client = MagicMock()
        mock_client.get_metric_data.return_value = {
            "MetricDataResults": [
                {
                    "Id": "m1",
                    "Label": "CPUUtilization",
                    "Timestamps": [
                        datetime(2026, 1, 29, 10, 0, 0, tzinfo=timezone.utc),
                        datetime(2026, 1, 29, 9, 55, 0, tzinfo=timezone.utc),
                    ],
                    "Values": [85.0, 72.0],
                    "StatusCode": "Complete",
                }
            ]
        }

        tool = GetMetricsTool(cloudwatch_client=mock_client)
        result = tool.execute(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={"InstanceId": "i-1234567890abcdef0"},
            period_minutes=60,
        )

        assert result["status"] == "success"
        assert len(result["datapoints"]) == 2
        assert result["datapoints"][0]["value"] == 85.0
        assert result["statistics"]["max"] == 85.0
        assert result["statistics"]["min"] == 72.0
        assert result["statistics"]["avg"] == 78.5

    def test_execute_handles_no_data(self):
        """Test tool handles case with no metric data."""
        mock_client = MagicMock()
        mock_client.get_metric_data.return_value = {
            "MetricDataResults": [{"Id": "m1", "Timestamps": [], "Values": []}]
        }

        tool = GetMetricsTool(cloudwatch_client=mock_client)
        result = tool.execute(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={"InstanceId": "i-nonexistent"},
            period_minutes=60,
        )

        assert result["status"] == "success"
        assert len(result["datapoints"]) == 0
        assert result["statistics"] == {}

    def test_execute_handles_error(self):
        """Test tool handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.get_metric_data.side_effect = Exception("API Error")

        tool = GetMetricsTool(cloudwatch_client=mock_client)
        result = tool.execute(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            period_minutes=60,
        )

        assert result["status"] == "error"
        assert "API Error" in result["error"]
