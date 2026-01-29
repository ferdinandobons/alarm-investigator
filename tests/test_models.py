"""Tests for alarm event models."""

import pytest

from alarm_investigator.models import AlarmEvent, AlarmState


class TestAlarmEvent:
    """Tests for AlarmEvent parsing."""

    def test_parse_cloudwatch_alarm_event(self):
        """Test parsing a CloudWatch alarm state change event."""
        raw_event = {
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
                    "reason": "Threshold Crossed: 1 datapoint (85.0) > 80.0",
                    "reasonData": (
                        '{"version":"1.0","queryDate":"2026-01-29T10:00:00Z",'
                        '"evaluatedDatapoints":[{"timestamp":"2026-01-29T09:55:00Z","value":85.0}]}'
                    ),
                    "timestamp": "2026-01-29T10:00:00.000+0000"
                },
                "previousState": {
                    "value": "OK",
                    "reason": "Threshold not crossed",
                    "timestamp": "2026-01-29T09:00:00.000+0000"
                },
                "configuration": {
                    "metrics": [
                        {
                            "id": "m1",
                            "metricStat": {
                                "metric": {
                                    "namespace": "AWS/EC2",
                                    "name": "CPUUtilization",
                                    "dimensions": {"InstanceId": "i-1234567890abcdef0"}
                                },
                                "period": 300,
                                "stat": "Average"
                            },
                            "returnData": True
                        }
                    ]
                }
            }
        }

        alarm = AlarmEvent.from_eventbridge(raw_event)

        assert alarm.alarm_name == "HighCPU"
        assert alarm.account_id == "123456789012"
        assert alarm.region == "us-east-1"
        assert alarm.state == AlarmState.ALARM
        assert alarm.previous_state == AlarmState.OK
        assert alarm.reason == "Threshold Crossed: 1 datapoint (85.0) > 80.0"
        assert alarm.namespace == "AWS/EC2"
        assert alarm.metric_name == "CPUUtilization"
        assert alarm.dimensions == {"InstanceId": "i-1234567890abcdef0"}

    def test_parse_alarm_event_insufficient_data(self):
        """Test parsing alarm with INSUFFICIENT_DATA state."""
        raw_event = {
            "version": "0",
            "id": "event-456",
            "detail-type": "CloudWatch Alarm State Change",
            "source": "aws.cloudwatch",
            "account": "123456789012",
            "time": "2026-01-29T10:00:00Z",
            "region": "eu-west-1",
            "resources": ["arn:aws:cloudwatch:eu-west-1:123456789012:alarm:NoData"],
            "detail": {
                "alarmName": "NoData",
                "state": {
                    "value": "INSUFFICIENT_DATA",
                    "reason": "No datapoints",
                    "timestamp": "2026-01-29T10:00:00.000+0000"
                },
                "previousState": {
                    "value": "OK",
                    "reason": "All good",
                    "timestamp": "2026-01-29T09:00:00.000+0000"
                },
                "configuration": {
                    "metrics": []
                }
            }
        }

        alarm = AlarmEvent.from_eventbridge(raw_event)

        assert alarm.state == AlarmState.INSUFFICIENT_DATA
        assert alarm.namespace is None
        assert alarm.metric_name is None

    def test_invalid_event_raises_error(self):
        """Test that invalid events raise ValueError."""
        with pytest.raises(ValueError, match="Invalid event"):
            AlarmEvent.from_eventbridge({"invalid": "event"})
