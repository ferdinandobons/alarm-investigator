"""Tests for tool base class and registry."""

from alarm_investigator.tools.base import Tool, ToolRegistry


class MockTool(Tool):
    """A mock tool for testing."""

    name = "mock_tool"
    description = "A mock tool for testing purposes"

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input_value": {"type": "string", "description": "Test input"}
            },
            "required": ["input_value"],
        }

    def execute(self, **kwargs) -> dict:
        return {"result": f"processed: {kwargs.get('input_value')}"}


class TestTool:
    """Tests for Tool base class."""

    def test_tool_to_bedrock_spec(self):
        """Test converting tool to Bedrock tool spec format."""
        tool = MockTool()
        spec = tool.to_bedrock_spec()

        assert spec == {
            "toolSpec": {
                "name": "mock_tool",
                "description": "A mock tool for testing purposes",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "input_value": {"type": "string", "description": "Test input"}
                        },
                        "required": ["input_value"],
                    }
                },
            }
        }

    def test_tool_execute(self):
        """Test tool execution."""
        tool = MockTool()
        result = tool.execute(input_value="hello")
        assert result == {"result": "processed: hello"}


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_and_get_tool(self):
        """Test registering and retrieving a tool."""
        registry = ToolRegistry()
        tool = MockTool()

        registry.register(tool)

        assert registry.get("mock_tool") is tool

    def test_get_unknown_tool_returns_none(self):
        """Test getting an unregistered tool returns None."""
        registry = ToolRegistry()
        assert registry.get("unknown") is None

    def test_get_all_tools(self):
        """Test getting all registered tools."""
        registry = ToolRegistry()
        tool = MockTool()
        registry.register(tool)

        tools = registry.get_all()

        assert len(tools) == 1
        assert tools[0] is tool

    def test_get_bedrock_tool_config(self):
        """Test generating Bedrock tool config from registry."""
        registry = ToolRegistry()
        registry.register(MockTool())

        config = registry.get_bedrock_config()

        assert "tools" in config
        assert len(config["tools"]) == 1
        assert config["tools"][0]["toolSpec"]["name"] == "mock_tool"
