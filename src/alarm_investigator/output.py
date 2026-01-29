"""Report formatting for investigation output."""

import html
from datetime import datetime, timezone

from alarm_investigator.models import AlarmEvent


class ReportFormatter:
    """Formats investigation reports for various outputs."""

    def format_email(self, alarm: AlarmEvent, analysis: str) -> dict:
        """Format report for email delivery."""
        subject = f"[{alarm.state.value}] Alarm Investigation: {alarm.alarm_name}"

        # Convert markdown to basic HTML
        html_analysis = self._markdown_to_html(analysis)

        # Pre-escape values for the template
        alarm_name = html.escape(alarm.alarm_name)
        account_id = html.escape(alarm.account_id)
        region = html.escape(alarm.region)
        state = html.escape(alarm.state.value)
        prev_state = html.escape(alarm.previous_state.value)
        namespace = html.escape(alarm.namespace or "N/A")
        metric_name = html.escape(alarm.metric_name or "N/A")
        dimensions = html.escape(str(alarm.dimensions or {}))
        reason = html.escape(alarm.reason)
        header_class = "header ok" if alarm.state.value == "OK" else "header"

        body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #f44336; color: white; padding: 20px; }}
        .header.ok {{ background: #4CAF50; }}
        .content {{ padding: 20px; }}
        .metadata {{ background: #f5f5f5; padding: 15px; margin: 20px 0; }}
        .metadata dt {{ font-weight: bold; }}
        h2 {{ color: #1976D2; border-bottom: 2px solid #1976D2; padding-bottom: 5px; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="{header_class}">
        <h1>Alarm Investigation Report</h1>
        <p>{alarm_name}</p>
    </div>
    <div class="content">
        <div class="metadata">
            <dl>
                <dt>Account</dt><dd>{account_id}</dd>
                <dt>Region</dt><dd>{region}</dd>
                <dt>State</dt><dd>{state} (was {prev_state})</dd>
                <dt>Metric</dt><dd>{namespace} / {metric_name}</dd>
                <dt>Dimensions</dt><dd>{dimensions}</dd>
                <dt>Reason</dt><dd>{reason}</dd>
            </dl>
        </div>
        <div class="analysis">
            {html_analysis}
        </div>
    </div>
</body>
</html>
"""

        return {
            "subject": subject,
            "body": body,
            "content_type": "text/html",
        }

    def format_json(self, alarm: AlarmEvent, analysis: str) -> dict:
        """Format report as JSON."""
        return {
            "alarm_name": alarm.alarm_name,
            "account_id": alarm.account_id,
            "region": alarm.region,
            "state": alarm.state.value,
            "previous_state": alarm.previous_state.value,
            "reason": alarm.reason,
            "namespace": alarm.namespace,
            "metric_name": alarm.metric_name,
            "dimensions": alarm.dimensions,
            "analysis": analysis,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _markdown_to_html(self, text: str) -> str:
        """Simple markdown to HTML conversion."""
        lines = text.split("\n")
        html_lines = []

        for line in lines:
            if line.startswith("## "):
                html_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{html.escape(line[4:])}</h3>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{html.escape(line[2:])}</li>")
            elif line.startswith("**") and line.endswith("**"):
                html_lines.append(f"<strong>{html.escape(line[2:-2])}</strong>")
            elif line.strip():
                html_lines.append(f"<p>{html.escape(line)}</p>")

        return "\n".join(html_lines)
