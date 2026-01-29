"""Tests for Lambda handler."""

import json
from unittest.mock import MagicMock, patch

from alarm_investigator.handler import lambda_handler


class TestLambdaHandler:
    """Tests for Lambda handler."""

    def create_eventbridge_event(self) -> dict:
        """Create a test EventBridge event."""
        return {
            "version": "0",
            "id": "event-123",
            "detail-type": "CloudWatch Alarm State Change",
            "source": "aws.cloudwatch",
            "account": "123456789012",
            "time": "2026-01-29T10:00:00Z",
            "region": "us-east-1",
            "resources": ["arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighCPU"],
            "detail": {
                "alarmName": "HighCPU",
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed",
                    "timestamp": "2026-01-29T10:00:00.000+0000",
                },
                "previousState": {
                    "value": "OK",
                    "reason": "All good",
                    "timestamp": "2026-01-29T09:00:00.000+0000",
                },
                "configuration": {
                    "metrics": [
                        {
                            "id": "m1",
                            "metricStat": {
                                "metric": {
                                    "namespace": "AWS/EC2",
                                    "name": "CPUUtilization",
                                    "dimensions": {"InstanceId": "i-1234567890abcdef0"},
                                },
                                "period": 300,
                                "stat": "Average",
                            },
                            "returnData": True,
                        }
                    ]
                },
            },
        }

    @patch("alarm_investigator.handler.boto3")
    def test_handler_processes_alarm_event(self, mock_boto3):
        """Test handler processes alarm event successfully."""
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "## Analysis\nRoot cause identified."}],
                }
            },
        }

        mock_sns = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {"Reservations": []}

        def get_client(service, **kwargs):
            clients = {
                "bedrock-runtime": mock_bedrock,
                "sns": mock_sns,
                "cloudwatch": mock_cloudwatch,
                "ec2": mock_ec2,
            }
            return clients.get(service, MagicMock())

        mock_boto3.client.side_effect = get_client

        event = self.create_eventbridge_event()
        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["alarm_name"] == "HighCPU"
        assert "analysis" in body

    @patch("alarm_investigator.handler.boto3")
    def test_handler_sends_sns_notification(self, mock_boto3):
        """Test handler sends SNS notification when topic configured."""
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Analysis complete."}],
                }
            },
        }

        mock_sns = MagicMock()
        mock_cloudwatch = MagicMock()

        def get_client(service, **kwargs):
            clients = {
                "bedrock-runtime": mock_bedrock,
                "sns": mock_sns,
                "cloudwatch": mock_cloudwatch,
            }
            return clients.get(service, MagicMock())

        mock_boto3.client.side_effect = get_client

        sns_arn = "arn:aws:sns:us-east-1:123456789012:alerts"
        with patch.dict("os.environ", {"SNS_TOPIC_ARN": sns_arn}):
            event = self.create_eventbridge_event()
            lambda_handler(event, None)

        mock_sns.publish.assert_called_once()

    @patch("alarm_investigator.handler.boto3")
    def test_handler_returns_error_on_invalid_event(self, mock_boto3):
        """Test handler returns error for invalid events."""
        event = {"invalid": "event"}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "error" in body
