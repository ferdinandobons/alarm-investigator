"""Tests for the Bedrock agent orchestrator."""

from unittest.mock import MagicMock

from alarm_investigator.agent import InvestigationAgent
from alarm_investigator.models import AlarmEvent, AlarmState
from alarm_investigator.tools.base import Tool, ToolRegistry


class MockTool(Tool):
    """Mock tool for testing."""

    name = "mock_tool"
    description = "A mock tool"

    def __init__(self):
        self.call_count = 0
        self.last_args = None

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"value": {"type": "string"}},
            "required": ["value"],
        }

    def execute(self, **kwargs) -> dict:
        self.call_count += 1
        self.last_args = kwargs
        return {"result": "mock_result"}


class TestInvestigationAgent:
    """Tests for InvestigationAgent."""

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

    def test_agent_creates_system_prompt(self):
        """Test agent generates appropriate system prompt."""
        registry = ToolRegistry()
        mock_bedrock = MagicMock()
        agent = InvestigationAgent(bedrock_client=mock_bedrock, tool_registry=registry)

        alarm = self.create_alarm_event()
        prompt = agent._build_system_prompt(alarm)

        assert "HighCPU" in prompt
        assert "CPUUtilization" in prompt
        assert "root cause" in prompt.lower()

    def test_agent_handles_tool_use_response(self):
        """Test agent executes tools when Bedrock requests them."""
        registry = ToolRegistry()
        mock_tool = MockTool()
        registry.register(mock_tool)

        mock_bedrock = MagicMock()
        # First call: Bedrock requests tool use
        mock_bedrock.converse.side_effect = [
            {
                "stopReason": "tool_use",
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [
                            {
                                "toolUse": {
                                    "toolUseId": "tool-123",
                                    "name": "mock_tool",
                                    "input": {"value": "test"},
                                }
                            }
                        ],
                    }
                },
            },
            # Second call: Bedrock returns final response
            {
                "stopReason": "end_turn",
                "output": {
                    "message": {
                        "role": "assistant",
                        "content": [{"text": "Based on my analysis, the root cause is..."}],
                    }
                },
            },
        ]

        agent = InvestigationAgent(bedrock_client=mock_bedrock, tool_registry=registry)
        alarm = self.create_alarm_event()

        result = agent.investigate(alarm)

        assert mock_tool.call_count == 1
        assert mock_tool.last_args == {"value": "test"}
        assert "root cause" in result.lower()

    def test_agent_returns_report_on_end_turn(self):
        """Test agent returns report when Bedrock ends turn."""
        registry = ToolRegistry()
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "## Root Cause Analysis\n\nThe issue is..."}],
                }
            },
        }

        agent = InvestigationAgent(bedrock_client=mock_bedrock, tool_registry=registry)
        alarm = self.create_alarm_event()

        result = agent.investigate(alarm)

        assert "Root Cause Analysis" in result

    def test_agent_limits_iterations(self):
        """Test agent stops after max iterations to prevent infinite loops."""
        registry = ToolRegistry()
        mock_tool = MockTool()
        registry.register(mock_tool)

        mock_bedrock = MagicMock()
        # Always request tool use (infinite loop scenario)
        mock_bedrock.converse.return_value = {
            "stopReason": "tool_use",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tool-123",
                                "name": "mock_tool",
                                "input": {"value": "test"},
                            }
                        }
                    ],
                }
            },
        }

        agent = InvestigationAgent(
            bedrock_client=mock_bedrock, tool_registry=registry, max_iterations=3
        )
        alarm = self.create_alarm_event()

        result = agent.investigate(alarm)

        assert mock_tool.call_count == 3
        assert "max iterations" in result.lower() or len(result) > 0
