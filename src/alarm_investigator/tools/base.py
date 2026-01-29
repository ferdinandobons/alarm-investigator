"""Base class and registry for investigation tools."""

from abc import ABC, abstractmethod


class Tool(ABC):
    """Base class for investigation tools."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def get_parameters_schema(self) -> dict:
        """Return JSON schema for tool parameters."""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """Execute the tool with given parameters."""
        pass

    def to_bedrock_spec(self) -> dict:
        """Convert tool to Bedrock toolSpec format."""
        return {
            "toolSpec": {
                "name": self.name,
                "description": self.description,
                "inputSchema": {"json": self.get_parameters_schema()},
            }
        }


class ToolRegistry:
    """Registry for managing investigation tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_all(self) -> list[Tool]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_bedrock_config(self) -> dict:
        """Generate Bedrock tool configuration."""
        return {"tools": [tool.to_bedrock_spec() for tool in self._tools.values()]}
