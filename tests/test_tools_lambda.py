"""Tests for Lambda tools."""

from unittest.mock import MagicMock

from alarm_investigator.tools.lambda_ import DescribeLambdaFunctionTool


class TestDescribeLambdaFunctionTool:
    """Tests for DescribeLambdaFunctionTool."""

    def test_tool_has_correct_spec(self):
        """Test tool has correct Bedrock spec."""
        tool = DescribeLambdaFunctionTool(lambda_client=MagicMock())
        spec = tool.to_bedrock_spec()

        assert spec["toolSpec"]["name"] == "describe_lambda_function"
        assert "function_name" in spec["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_execute_returns_function_info(self):
        """Test executing tool returns function information."""
        mock_client = MagicMock()
        mock_client.get_function.return_value = {
            "Configuration": {
                "FunctionName": "my-function",
                "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:my-function",
                "Runtime": "python3.12",
                "Handler": "handler.lambda_handler",
                "MemorySize": 256,
                "Timeout": 30,
                "State": "Active",
                "LastModified": "2026-01-15T10:00:00.000+0000",
                "Environment": {"Variables": {"LOG_LEVEL": "INFO"}},
            }
        }

        tool = DescribeLambdaFunctionTool(lambda_client=mock_client)
        result = tool.execute(function_name="my-function")

        assert result["status"] == "success"
        assert result["function"]["name"] == "my-function"
        assert result["function"]["runtime"] == "python3.12"
        assert result["function"]["memory_mb"] == 256
        assert result["function"]["timeout_seconds"] == 30
        assert result["function"]["state"] == "Active"

    def test_execute_handles_not_found(self):
        """Test tool handles function not found."""
        mock_client = MagicMock()
        mock_client.get_function.side_effect = Exception("Function not found")

        tool = DescribeLambdaFunctionTool(lambda_client=mock_client)
        result = tool.execute(function_name="nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()
