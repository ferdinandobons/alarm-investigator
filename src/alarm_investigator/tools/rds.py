"""RDS investigation tools."""

from alarm_investigator.tools.base import Tool


class DescribeRDSInstanceTool(Tool):
    """Tool to describe an RDS database instance."""

    name = "describe_rds_instance"
    description = (
        "Get detailed information about an RDS database instance including its "
        "status, configuration, storage, and endpoint. Use this to understand "
        "database health and configuration related to an alarm."
    )

    def __init__(self, rds_client):
        self._client = rds_client

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "db_instance_identifier": {
                    "type": "string",
                    "description": "The RDS DB instance identifier",
                }
            },
            "required": ["db_instance_identifier"],
        }

    def execute(self, db_instance_identifier: str, **kwargs) -> dict:
        """Describe an RDS DB instance."""
        try:
            response = self._client.describe_db_instances(
                DBInstanceIdentifier=db_instance_identifier
            )

            instances = response.get("DBInstances", [])
            if not instances:
                return {
                    "status": "error",
                    "error": f"DB instance {db_instance_identifier} not found",
                }

            db = instances[0]
            endpoint = db.get("Endpoint", {})

            return {
                "status": "success",
                "db_instance": {
                    "identifier": db["DBInstanceIdentifier"],
                    "instance_class": db.get("DBInstanceClass"),
                    "engine": db.get("Engine"),
                    "engine_version": db.get("EngineVersion"),
                    "status": db.get("DBInstanceStatus"),
                    "allocated_storage_gb": db.get("AllocatedStorage"),
                    "storage_type": db.get("StorageType"),
                    "multi_az": db.get("MultiAZ", False),
                    "endpoint": endpoint.get("Address"),
                    "port": endpoint.get("Port"),
                    "arn": db.get("DBInstanceArn"),
                },
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
