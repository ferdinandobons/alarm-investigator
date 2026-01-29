"""ECS investigation tools."""

from alarm_investigator.tools.base import Tool


class DescribeECSServiceTool(Tool):
    """Tool to describe an ECS service."""

    name = "describe_ecs_service"
    description = (
        "Get detailed information about an ECS service including its status, "
        "task counts, and deployment state. Use this to understand service "
        "health and configuration related to an alarm."
    )

    def __init__(self, ecs_client):
        self._client = ecs_client

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "cluster": {
                    "type": "string",
                    "description": "The ECS cluster name or ARN",
                },
                "service": {
                    "type": "string",
                    "description": "The ECS service name or ARN",
                },
            },
            "required": ["cluster", "service"],
        }

    def execute(self, cluster: str, service: str, **kwargs) -> dict:
        """Describe an ECS service."""
        try:
            response = self._client.describe_services(
                cluster=cluster, services=[service]
            )

            services = response.get("services", [])
            if not services:
                return {
                    "status": "error",
                    "error": f"Service {service} not found in cluster {cluster}",
                }

            svc = services[0]
            deployments = svc.get("deployments", [])

            return {
                "status": "success",
                "service": {
                    "name": svc["serviceName"],
                    "arn": svc.get("serviceArn"),
                    "status": svc.get("status"),
                    "desired_count": svc.get("desiredCount"),
                    "running_count": svc.get("runningCount"),
                    "pending_count": svc.get("pendingCount"),
                    "launch_type": svc.get("launchType"),
                    "deployments": [
                        {
                            "id": d.get("id"),
                            "status": d.get("status"),
                            "desired": d.get("desiredCount"),
                            "running": d.get("runningCount"),
                            "rollout_state": d.get("rolloutState"),
                        }
                        for d in deployments
                    ],
                },
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
