"""CloudWatch investigation tools."""

from datetime import datetime, timedelta, timezone

from alarm_investigator.tools.base import Tool


class GetMetricsTool(Tool):
    """Tool to retrieve CloudWatch metric data."""

    name = "get_cloudwatch_metrics"
    description = (
        "Retrieve CloudWatch metric data for a specific metric. "
        "Use this to analyze metric trends and values around the time of an alarm."
    )

    def __init__(self, cloudwatch_client):
        self._client = cloudwatch_client

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string",
                    "description": "AWS namespace (e.g., AWS/EC2, AWS/RDS)",
                },
                "metric_name": {
                    "type": "string",
                    "description": "Name of the metric (e.g., CPUUtilization)",
                },
                "dimensions": {
                    "type": "object",
                    "description": "Metric dimensions as key-value pairs",
                    "additionalProperties": {"type": "string"},
                },
                "period_minutes": {
                    "type": "integer",
                    "description": "How many minutes of data to retrieve (default: 60)",
                    "default": 60,
                },
            },
            "required": ["namespace", "metric_name", "dimensions"],
        }

    def execute(
        self,
        namespace: str,
        metric_name: str,
        dimensions: dict,
        period_minutes: int = 60,
        **kwargs,
    ) -> dict:
        """Retrieve metric data from CloudWatch."""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=period_minutes)

            dimension_list = [{"Name": k, "Value": v} for k, v in dimensions.items()]

            response = self._client.get_metric_data(
                MetricDataQueries=[
                    {
                        "Id": "m1",
                        "MetricStat": {
                            "Metric": {
                                "Namespace": namespace,
                                "MetricName": metric_name,
                                "Dimensions": dimension_list,
                            },
                            "Period": 300,  # 5-minute granularity
                            "Stat": "Average",
                        },
                        "ReturnData": True,
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
            )

            results = response.get("MetricDataResults", [])
            if not results:
                return {"status": "success", "datapoints": [], "statistics": {}}

            metric_result = results[0]
            timestamps = metric_result.get("Timestamps", [])
            values = metric_result.get("Values", [])

            datapoints = [
                {"timestamp": ts.isoformat(), "value": val}
                for ts, val in zip(timestamps, values)
            ]

            statistics = {}
            if values:
                statistics = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values),
                }

            return {
                "status": "success",
                "namespace": namespace,
                "metric_name": metric_name,
                "datapoints": datapoints,
                "statistics": statistics,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
