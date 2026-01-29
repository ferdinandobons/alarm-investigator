"""Data models for alarm events."""

from dataclasses import dataclass
from enum import Enum


class AlarmState(Enum):
    """CloudWatch alarm states."""

    OK = "OK"
    ALARM = "ALARM"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class AlarmEvent:
    """Parsed CloudWatch alarm event from EventBridge."""

    alarm_name: str
    account_id: str
    region: str
    state: AlarmState
    previous_state: AlarmState
    reason: str
    namespace: str | None
    metric_name: str | None
    dimensions: dict[str, str] | None
    raw_event: dict

    @classmethod
    def from_eventbridge(cls, event: dict) -> "AlarmEvent":
        """Parse an EventBridge CloudWatch alarm event."""
        if "detail" not in event or "alarmName" not in event.get("detail", {}):
            raise ValueError("Invalid event: missing required fields")

        detail = event["detail"]
        state_info = detail["state"]
        previous_state_info = detail.get("previousState", {})
        config = detail.get("configuration", {})
        metrics = config.get("metrics", [])

        # Extract metric info from first metric if available
        namespace = None
        metric_name = None
        dimensions = None

        if metrics:
            first_metric = metrics[0]
            metric_stat = first_metric.get("metricStat", {})
            metric_info = metric_stat.get("metric", {})
            namespace = metric_info.get("namespace")
            metric_name = metric_info.get("name")
            dimensions = metric_info.get("dimensions")

        return cls(
            alarm_name=detail["alarmName"],
            account_id=event["account"],
            region=event["region"],
            state=AlarmState(state_info["value"]),
            previous_state=AlarmState(previous_state_info.get("value", "OK")),
            reason=state_info.get("reason", ""),
            namespace=namespace,
            metric_name=metric_name,
            dimensions=dimensions,
            raw_event=event,
        )
