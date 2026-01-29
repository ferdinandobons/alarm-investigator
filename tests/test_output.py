"""Tests for output formatting."""

from alarm_investigator.models import AlarmEvent, AlarmState
from alarm_investigator.output import ReportFormatter


class TestReportFormatter:
    """Tests for ReportFormatter."""

    def create_alarm_event(self) -> AlarmEvent:
        """Create a test alarm event."""
        return AlarmEvent(
            alarm_name="HighCPU",
            account_id="123456789012",
            region="us-east-1",
            state=AlarmState.ALARM,
            previous_state=AlarmState.OK,
            reason="Threshold Crossed: CPU > 80%",
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={"InstanceId": "i-1234567890abcdef0"},
            raw_event={},
        )

    def test_format_email_report(self):
        """Test formatting report for email."""
        alarm = self.create_alarm_event()
        analysis = """## Summary
High CPU utilization on instance i-1234567890abcdef0.

## Root Cause
Application processing spike due to batch job."""

        formatter = ReportFormatter()
        result = formatter.format_email(alarm, analysis)

        assert "HighCPU" in result["subject"]
        assert "ALARM" in result["subject"]
        assert "High CPU utilization" in result["body"]
        assert "Root Cause" in result["body"]
        assert result["content_type"] == "text/html"

    def test_format_email_includes_alarm_metadata(self):
        """Test email includes alarm metadata."""
        alarm = self.create_alarm_event()
        analysis = "Test analysis"

        formatter = ReportFormatter()
        result = formatter.format_email(alarm, analysis)

        assert "123456789012" in result["body"]
        assert "us-east-1" in result["body"]
        assert "i-1234567890abcdef0" in result["body"]

    def test_format_json_report(self):
        """Test formatting report as JSON."""
        alarm = self.create_alarm_event()
        analysis = "Test analysis"

        formatter = ReportFormatter()
        result = formatter.format_json(alarm, analysis)

        assert result["alarm_name"] == "HighCPU"
        assert result["state"] == "ALARM"
        assert result["analysis"] == "Test analysis"
        assert "timestamp" in result
