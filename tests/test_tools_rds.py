"""Tests for RDS tools."""

from unittest.mock import MagicMock

from alarm_investigator.tools.rds import DescribeRDSInstanceTool


class TestDescribeRDSInstanceTool:
    """Tests for DescribeRDSInstanceTool."""

    def test_tool_has_correct_spec(self):
        """Test tool has correct Bedrock spec."""
        tool = DescribeRDSInstanceTool(rds_client=MagicMock())
        spec = tool.to_bedrock_spec()

        assert spec["toolSpec"]["name"] == "describe_rds_instance"
        assert "db_instance_identifier" in spec["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_execute_returns_db_info(self):
        """Test executing tool returns DB instance information."""
        mock_client = MagicMock()
        mock_client.describe_db_instances.return_value = {
            "DBInstances": [
                {
                    "DBInstanceIdentifier": "mydb",
                    "DBInstanceClass": "db.t3.medium",
                    "Engine": "postgres",
                    "EngineVersion": "15.4",
                    "DBInstanceStatus": "available",
                    "AllocatedStorage": 100,
                    "StorageType": "gp3",
                    "MultiAZ": True,
                    "Endpoint": {
                        "Address": "mydb.xxx.us-east-1.rds.amazonaws.com",
                        "Port": 5432,
                    },
                    "DBInstanceArn": "arn:aws:rds:us-east-1:123456789012:db:mydb",
                }
            ]
        }

        tool = DescribeRDSInstanceTool(rds_client=mock_client)
        result = tool.execute(db_instance_identifier="mydb")

        assert result["status"] == "success"
        assert result["db_instance"]["identifier"] == "mydb"
        assert result["db_instance"]["instance_class"] == "db.t3.medium"
        assert result["db_instance"]["engine"] == "postgres"
        assert result["db_instance"]["status"] == "available"
        assert result["db_instance"]["multi_az"] is True

    def test_execute_handles_not_found(self):
        """Test tool handles DB instance not found."""
        mock_client = MagicMock()
        mock_client.describe_db_instances.return_value = {"DBInstances": []}

        tool = DescribeRDSInstanceTool(rds_client=mock_client)
        result = tool.execute(db_instance_identifier="nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_execute_handles_api_error(self):
        """Test tool handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.describe_db_instances.side_effect = Exception("Access Denied")

        tool = DescribeRDSInstanceTool(rds_client=mock_client)
        result = tool.execute(db_instance_identifier="mydb")

        assert result["status"] == "error"
        assert "Access Denied" in result["error"]
