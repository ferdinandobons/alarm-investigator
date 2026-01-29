"""Lambda investigation tools."""

from alarm_investigator.tools.base import Tool


class DescribeLambdaFunctionTool(Tool):
    """Tool to describe a Lambda function."""

    name = "describe_lambda_function"
    description = (
        "Get detailed information about a Lambda function including its "
        "configuration, memory, timeout, and state. Use this to understand "
        "function settings related to an alarm."
    )

    def __init__(self, lambda_client):
        self._client = lambda_client

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "function_name": {
                    "type": "string",
                    "description": "The Lambda function name or ARN",
                }
            },
            "required": ["function_name"],
        }

    def execute(self, function_name: str, **kwargs) -> dict:
        """Describe a Lambda function."""
        try:
            response = self._client.get_function(FunctionName=function_name)

            config = response.get("Configuration", {})
            env_vars = config.get("Environment", {}).get("Variables", {})

            return {
                "status": "success",
                "function": {
                    "name": config["FunctionName"],
                    "arn": config.get("FunctionArn"),
                    "runtime": config.get("Runtime"),
                    "handler": config.get("Handler"),
                    "memory_mb": config.get("MemorySize"),
                    "timeout_seconds": config.get("Timeout"),
                    "state": config.get("State"),
                    "last_modified": config.get("LastModified"),
                    "environment_variables": list(env_vars.keys()),
                },
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
