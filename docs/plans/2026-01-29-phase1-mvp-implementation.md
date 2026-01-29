# Alarm Investigator - Phase 1 MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone open-source agent that investigates CloudWatch alarms using Claude Sonnet on Bedrock and produces root cause analysis reports.

**Architecture:** Lambda receives CloudWatch alarm events via EventBridge, invokes Bedrock Converse API with tool use to investigate AWS resources, and outputs a structured report via SNS email.

**Tech Stack:** Python 3.12, boto3, AWS Lambda, EventBridge, Bedrock (Claude Sonnet), SNS, Terraform

---

## Task 1: Project Setup

**Files:**
- Create: `src/alarm_investigator/__init__.py`
- Create: `src/alarm_investigator/handler.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`

**Step 1: Create project structure**

```bash
mkdir -p src/alarm_investigator tests
```

**Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "alarm-investigator"
version = "0.1.0"
description = "AI-powered CloudWatch alarm investigation agent"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.12"
dependencies = [
    "boto3>=1.35.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "moto>=5.0.0",
    "ruff>=0.4.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
```

**Step 3: Create requirements.txt**

```
boto3>=1.35.0
```

**Step 4: Create requirements-dev.txt**

```
-r requirements.txt
pytest>=8.0.0
pytest-cov>=4.0.0
moto>=5.0.0
ruff>=0.4.0
```

**Step 5: Create .gitignore**

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
.venv
env/
venv/
.pytest_cache/
.coverage
htmlcov/
.terraform/
*.tfstate
*.tfstate.*
.terraform.lock.hcl
```

**Step 6: Create src/alarm_investigator/__init__.py**

```python
"""Alarm Investigator - AI-powered CloudWatch alarm investigation agent."""

__version__ = "0.1.0"
```

**Step 7: Create empty handler placeholder**

```python
"""Lambda handler for Alarm Investigator."""


def lambda_handler(event: dict, context) -> dict:
    """Main Lambda entry point."""
    raise NotImplementedError("Handler not yet implemented")
```

**Step 8: Create tests/__init__.py**

```python
"""Tests for Alarm Investigator."""
```

**Step 9: Create tests/conftest.py**

```python
"""Pytest configuration and fixtures."""

import os

import pytest


@pytest.fixture(autouse=True)
def aws_credentials():
    """Mock AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
```

**Step 10: Verify setup**

Run: `python -c "import sys; print(sys.version)"`
Expected: Python 3.12.x

**Step 11: Install dependencies**

Run: `pip install -e ".[dev]"`
Expected: Successfully installed packages

**Step 12: Run initial test (should pass with no tests)**

Run: `pytest`
Expected: "no tests ran" or similar

**Step 13: Commit**

```bash
git add -A
git commit -m "chore: initialize project structure with pytest and dependencies"
```

---

## Task 2: Alarm Event Parser

**Files:**
- Create: `src/alarm_investigator/models.py`
- Create: `tests/test_models.py`

**Step 1: Write the failing test for AlarmEvent model**

```python
"""Tests for alarm event models."""

import pytest

from alarm_investigator.models import AlarmEvent, AlarmState


class TestAlarmEvent:
    """Tests for AlarmEvent parsing."""

    def test_parse_cloudwatch_alarm_event(self):
        """Test parsing a CloudWatch alarm state change event."""
        raw_event = {
            "version": "0",
            "id": "event-123",
            "detail-type": "CloudWatch Alarm State Change",
            "source": "aws.cloudwatch",
            "account": "123456789012",
            "time": "2026-01-29T10:00:00Z",
            "region": "us-east-1",
            "resources": ["arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighCPU"],
            "detail": {
                "alarmName": "HighCPU",
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed: 1 datapoint (85.0) > 80.0",
                    "reasonData": '{"version":"1.0","queryDate":"2026-01-29T10:00:00Z","evaluatedDatapoints":[{"timestamp":"2026-01-29T09:55:00Z","value":85.0}]}',
                    "timestamp": "2026-01-29T10:00:00.000+0000"
                },
                "previousState": {
                    "value": "OK",
                    "reason": "Threshold not crossed",
                    "timestamp": "2026-01-29T09:00:00.000+0000"
                },
                "configuration": {
                    "metrics": [
                        {
                            "id": "m1",
                            "metricStat": {
                                "metric": {
                                    "namespace": "AWS/EC2",
                                    "name": "CPUUtilization",
                                    "dimensions": {"InstanceId": "i-1234567890abcdef0"}
                                },
                                "period": 300,
                                "stat": "Average"
                            },
                            "returnData": True
                        }
                    ]
                }
            }
        }

        alarm = AlarmEvent.from_eventbridge(raw_event)

        assert alarm.alarm_name == "HighCPU"
        assert alarm.account_id == "123456789012"
        assert alarm.region == "us-east-1"
        assert alarm.state == AlarmState.ALARM
        assert alarm.previous_state == AlarmState.OK
        assert alarm.reason == "Threshold Crossed: 1 datapoint (85.0) > 80.0"
        assert alarm.namespace == "AWS/EC2"
        assert alarm.metric_name == "CPUUtilization"
        assert alarm.dimensions == {"InstanceId": "i-1234567890abcdef0"}

    def test_parse_alarm_event_insufficient_data(self):
        """Test parsing alarm with INSUFFICIENT_DATA state."""
        raw_event = {
            "version": "0",
            "id": "event-456",
            "detail-type": "CloudWatch Alarm State Change",
            "source": "aws.cloudwatch",
            "account": "123456789012",
            "time": "2026-01-29T10:00:00Z",
            "region": "eu-west-1",
            "resources": ["arn:aws:cloudwatch:eu-west-1:123456789012:alarm:NoData"],
            "detail": {
                "alarmName": "NoData",
                "state": {
                    "value": "INSUFFICIENT_DATA",
                    "reason": "No datapoints",
                    "timestamp": "2026-01-29T10:00:00.000+0000"
                },
                "previousState": {
                    "value": "OK",
                    "reason": "All good",
                    "timestamp": "2026-01-29T09:00:00.000+0000"
                },
                "configuration": {
                    "metrics": []
                }
            }
        }

        alarm = AlarmEvent.from_eventbridge(raw_event)

        assert alarm.state == AlarmState.INSUFFICIENT_DATA
        assert alarm.namespace is None
        assert alarm.metric_name is None

    def test_invalid_event_raises_error(self):
        """Test that invalid events raise ValueError."""
        with pytest.raises(ValueError, match="Invalid event"):
            AlarmEvent.from_eventbridge({"invalid": "event"})
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'alarm_investigator.models'"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/alarm_investigator/models.py tests/test_models.py
git commit -m "feat: add AlarmEvent model with EventBridge parsing"
```

---

## Task 3: Tool Base Class and Registry

**Files:**
- Create: `src/alarm_investigator/tools/__init__.py`
- Create: `src/alarm_investigator/tools/base.py`
- Create: `tests/test_tools_base.py`

**Step 1: Write the failing test for Tool base class**

```python
"""Tests for tool base class and registry."""

import pytest

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools_base.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create tools directory**

```bash
mkdir -p src/alarm_investigator/tools
```

**Step 4: Create src/alarm_investigator/tools/__init__.py**

```python
"""Investigation tools for the alarm agent."""

from alarm_investigator.tools.base import Tool, ToolRegistry

__all__ = ["Tool", "ToolRegistry"]
```

**Step 5: Write minimal implementation**

```python
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
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/test_tools_base.py -v`
Expected: PASS (6 tests)

**Step 7: Commit**

```bash
git add src/alarm_investigator/tools/ tests/test_tools_base.py
git commit -m "feat: add Tool base class and ToolRegistry"
```

---

## Task 4: CloudWatch Metrics Tool

**Files:**
- Create: `src/alarm_investigator/tools/cloudwatch.py`
- Create: `tests/test_tools_cloudwatch.py`

**Step 1: Write the failing test**

```python
"""Tests for CloudWatch tools."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from alarm_investigator.tools.cloudwatch import GetMetricsTool


class TestGetMetricsTool:
    """Tests for GetMetricsTool."""

    def test_tool_has_correct_spec(self):
        """Test tool has correct Bedrock spec."""
        tool = GetMetricsTool(cloudwatch_client=MagicMock())
        spec = tool.to_bedrock_spec()

        assert spec["toolSpec"]["name"] == "get_cloudwatch_metrics"
        assert "namespace" in spec["toolSpec"]["inputSchema"]["json"]["properties"]
        assert "metric_name" in spec["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_execute_returns_metric_data(self):
        """Test executing tool returns metric data."""
        mock_client = MagicMock()
        mock_client.get_metric_data.return_value = {
            "MetricDataResults": [
                {
                    "Id": "m1",
                    "Label": "CPUUtilization",
                    "Timestamps": [
                        datetime(2026, 1, 29, 10, 0, 0, tzinfo=timezone.utc),
                        datetime(2026, 1, 29, 9, 55, 0, tzinfo=timezone.utc),
                    ],
                    "Values": [85.0, 72.0],
                    "StatusCode": "Complete",
                }
            ]
        }

        tool = GetMetricsTool(cloudwatch_client=mock_client)
        result = tool.execute(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={"InstanceId": "i-1234567890abcdef0"},
            period_minutes=60,
        )

        assert result["status"] == "success"
        assert len(result["datapoints"]) == 2
        assert result["datapoints"][0]["value"] == 85.0
        assert result["statistics"]["max"] == 85.0
        assert result["statistics"]["min"] == 72.0
        assert result["statistics"]["avg"] == 78.5

    def test_execute_handles_no_data(self):
        """Test tool handles case with no metric data."""
        mock_client = MagicMock()
        mock_client.get_metric_data.return_value = {"MetricDataResults": [{"Id": "m1", "Timestamps": [], "Values": []}]}

        tool = GetMetricsTool(cloudwatch_client=mock_client)
        result = tool.execute(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={"InstanceId": "i-nonexistent"},
            period_minutes=60,
        )

        assert result["status"] == "success"
        assert len(result["datapoints"]) == 0
        assert result["statistics"] == {}

    def test_execute_handles_error(self):
        """Test tool handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.get_metric_data.side_effect = Exception("API Error")

        tool = GetMetricsTool(cloudwatch_client=mock_client)
        result = tool.execute(
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            period_minutes=60,
        )

        assert result["status"] == "error"
        assert "API Error" in result["error"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools_cloudwatch.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools_cloudwatch.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/alarm_investigator/tools/cloudwatch.py tests/test_tools_cloudwatch.py
git commit -m "feat: add GetMetricsTool for CloudWatch metric retrieval"
```

---

## Task 5: EC2 Describe Tool

**Files:**
- Create: `src/alarm_investigator/tools/ec2.py`
- Create: `tests/test_tools_ec2.py`

**Step 1: Write the failing test**

```python
"""Tests for EC2 tools."""

from unittest.mock import MagicMock

import pytest

from alarm_investigator.tools.ec2 import DescribeEC2InstanceTool


class TestDescribeEC2InstanceTool:
    """Tests for DescribeEC2InstanceTool."""

    def test_tool_has_correct_spec(self):
        """Test tool has correct Bedrock spec."""
        tool = DescribeEC2InstanceTool(ec2_client=MagicMock())
        spec = tool.to_bedrock_spec()

        assert spec["toolSpec"]["name"] == "describe_ec2_instance"
        assert "instance_id" in spec["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_execute_returns_instance_info(self):
        """Test executing tool returns instance information."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "InstanceType": "t3.medium",
                            "State": {"Name": "running"},
                            "LaunchTime": "2026-01-01T00:00:00Z",
                            "PrivateIpAddress": "10.0.1.100",
                            "PublicIpAddress": "54.1.2.3",
                            "VpcId": "vpc-12345",
                            "SubnetId": "subnet-12345",
                            "Tags": [{"Key": "Name", "Value": "WebServer"}],
                        }
                    ]
                }
            ]
        }

        tool = DescribeEC2InstanceTool(ec2_client=mock_client)
        result = tool.execute(instance_id="i-1234567890abcdef0")

        assert result["status"] == "success"
        assert result["instance"]["instance_id"] == "i-1234567890abcdef0"
        assert result["instance"]["instance_type"] == "t3.medium"
        assert result["instance"]["state"] == "running"
        assert result["instance"]["name"] == "WebServer"

    def test_execute_handles_not_found(self):
        """Test tool handles instance not found."""
        mock_client = MagicMock()
        mock_client.describe_instances.return_value = {"Reservations": []}

        tool = DescribeEC2InstanceTool(ec2_client=mock_client)
        result = tool.execute(instance_id="i-nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_execute_handles_api_error(self):
        """Test tool handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.describe_instances.side_effect = Exception("Access Denied")

        tool = DescribeEC2InstanceTool(ec2_client=mock_client)
        result = tool.execute(instance_id="i-1234567890abcdef0")

        assert result["status"] == "error"
        assert "Access Denied" in result["error"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools_ec2.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
"""EC2 investigation tools."""

from alarm_investigator.tools.base import Tool


class DescribeEC2InstanceTool(Tool):
    """Tool to describe an EC2 instance."""

    name = "describe_ec2_instance"
    description = (
        "Get detailed information about an EC2 instance including its state, "
        "type, network configuration, and tags. Use this to understand the "
        "current state and configuration of an instance related to an alarm."
    )

    def __init__(self, ec2_client):
        self._client = ec2_client

    def get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "instance_id": {
                    "type": "string",
                    "description": "The EC2 instance ID (e.g., i-1234567890abcdef0)",
                }
            },
            "required": ["instance_id"],
        }

    def execute(self, instance_id: str, **kwargs) -> dict:
        """Describe an EC2 instance."""
        try:
            response = self._client.describe_instances(InstanceIds=[instance_id])

            reservations = response.get("Reservations", [])
            if not reservations or not reservations[0].get("Instances"):
                return {"status": "error", "error": f"Instance {instance_id} not found"}

            instance = reservations[0]["Instances"][0]

            # Extract name from tags
            name = None
            for tag in instance.get("Tags", []):
                if tag["Key"] == "Name":
                    name = tag["Value"]
                    break

            return {
                "status": "success",
                "instance": {
                    "instance_id": instance["InstanceId"],
                    "instance_type": instance.get("InstanceType"),
                    "state": instance.get("State", {}).get("Name"),
                    "launch_time": str(instance.get("LaunchTime", "")),
                    "private_ip": instance.get("PrivateIpAddress"),
                    "public_ip": instance.get("PublicIpAddress"),
                    "vpc_id": instance.get("VpcId"),
                    "subnet_id": instance.get("SubnetId"),
                    "name": name,
                    "tags": {
                        tag["Key"]: tag["Value"] for tag in instance.get("Tags", [])
                    },
                },
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools_ec2.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/alarm_investigator/tools/ec2.py tests/test_tools_ec2.py
git commit -m "feat: add DescribeEC2InstanceTool"
```

---

## Task 6: RDS Describe Tool

**Files:**
- Create: `src/alarm_investigator/tools/rds.py`
- Create: `tests/test_tools_rds.py`

**Step 1: Write the failing test**

```python
"""Tests for RDS tools."""

from unittest.mock import MagicMock

import pytest

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools_rds.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools_rds.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/alarm_investigator/tools/rds.py tests/test_tools_rds.py
git commit -m "feat: add DescribeRDSInstanceTool"
```

---

## Task 7: Lambda Describe Tool

**Files:**
- Create: `src/alarm_investigator/tools/lambda_.py`
- Create: `tests/test_tools_lambda.py`

**Step 1: Write the failing test**

```python
"""Tests for Lambda tools."""

from unittest.mock import MagicMock

import pytest

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools_lambda.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools_lambda.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/alarm_investigator/tools/lambda_.py tests/test_tools_lambda.py
git commit -m "feat: add DescribeLambdaFunctionTool"
```

---

## Task 8: ECS Describe Tools

**Files:**
- Create: `src/alarm_investigator/tools/ecs.py`
- Create: `tests/test_tools_ecs.py`

**Step 1: Write the failing test**

```python
"""Tests for ECS tools."""

from unittest.mock import MagicMock

import pytest

from alarm_investigator.tools.ecs import DescribeECSServiceTool


class TestDescribeECSServiceTool:
    """Tests for DescribeECSServiceTool."""

    def test_tool_has_correct_spec(self):
        """Test tool has correct Bedrock spec."""
        tool = DescribeECSServiceTool(ecs_client=MagicMock())
        spec = tool.to_bedrock_spec()

        assert spec["toolSpec"]["name"] == "describe_ecs_service"
        assert "cluster" in spec["toolSpec"]["inputSchema"]["json"]["properties"]
        assert "service" in spec["toolSpec"]["inputSchema"]["json"]["properties"]

    def test_execute_returns_service_info(self):
        """Test executing tool returns service information."""
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {
            "services": [
                {
                    "serviceName": "my-service",
                    "serviceArn": "arn:aws:ecs:us-east-1:123456789012:service/my-cluster/my-service",
                    "status": "ACTIVE",
                    "desiredCount": 3,
                    "runningCount": 3,
                    "pendingCount": 0,
                    "launchType": "FARGATE",
                    "deployments": [
                        {
                            "id": "ecs-svc/123",
                            "status": "PRIMARY",
                            "desiredCount": 3,
                            "runningCount": 3,
                            "rolloutState": "COMPLETED",
                        }
                    ],
                }
            ]
        }

        tool = DescribeECSServiceTool(ecs_client=mock_client)
        result = tool.execute(cluster="my-cluster", service="my-service")

        assert result["status"] == "success"
        assert result["service"]["name"] == "my-service"
        assert result["service"]["status"] == "ACTIVE"
        assert result["service"]["desired_count"] == 3
        assert result["service"]["running_count"] == 3
        assert result["service"]["launch_type"] == "FARGATE"

    def test_execute_handles_not_found(self):
        """Test tool handles service not found."""
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {"services": [], "failures": [{"reason": "MISSING"}]}

        tool = DescribeECSServiceTool(ecs_client=mock_client)
        result = tool.execute(cluster="my-cluster", service="nonexistent")

        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    def test_execute_handles_api_error(self):
        """Test tool handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.describe_services.side_effect = Exception("Access Denied")

        tool = DescribeECSServiceTool(ecs_client=mock_client)
        result = tool.execute(cluster="my-cluster", service="my-service")

        assert result["status"] == "error"
        assert "Access Denied" in result["error"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools_ecs.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_tools_ecs.py -v`
Expected: PASS (4 tests)

**Step 5: Commit**

```bash
git add src/alarm_investigator/tools/ecs.py tests/test_tools_ecs.py
git commit -m "feat: add DescribeECSServiceTool"
```

---

## Task 9: Bedrock Agent Orchestrator

**Files:**
- Create: `src/alarm_investigator/agent.py`
- Create: `tests/test_agent.py`

**Step 1: Write the failing test**

```python
"""Tests for the Bedrock agent orchestrator."""

from unittest.mock import MagicMock

import pytest

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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
"""Bedrock agent orchestrator for alarm investigation."""

from alarm_investigator.models import AlarmEvent
from alarm_investigator.tools.base import ToolRegistry


class InvestigationAgent:
    """Agent that investigates CloudWatch alarms using Bedrock."""

    MODEL_ID = "anthropic.claude-sonnet-4-20250514"

    def __init__(
        self,
        bedrock_client,
        tool_registry: ToolRegistry,
        max_iterations: int = 10,
    ):
        self._client = bedrock_client
        self._registry = tool_registry
        self._max_iterations = max_iterations

    def _build_system_prompt(self, alarm: AlarmEvent) -> str:
        """Build the system prompt for investigation."""
        return f"""You are an AWS infrastructure expert investigating a CloudWatch alarm.

## Alarm Details
- **Alarm Name:** {alarm.alarm_name}
- **State:** {alarm.state.value}
- **Previous State:** {alarm.previous_state.value}
- **Reason:** {alarm.reason}
- **Namespace:** {alarm.namespace or 'N/A'}
- **Metric:** {alarm.metric_name or 'N/A'}
- **Dimensions:** {alarm.dimensions or {}}
- **Account:** {alarm.account_id}
- **Region:** {alarm.region}

## Your Task
1. Use the available tools to gather information about the affected resources
2. Analyze metrics, configurations, and related resources
3. Identify the root cause of the alarm
4. Provide a clear, actionable report

## Output Format
Provide your analysis as a structured report with:
- **Summary:** One-sentence description of the issue
- **Root Cause:** What caused the alarm to trigger
- **Evidence:** Data points that support your conclusion
- **Recommendations:** Suggested actions to resolve or prevent the issue

Be concise but thorough. Focus on actionable insights."""

    def investigate(self, alarm: AlarmEvent) -> str:
        """Investigate an alarm and return a report."""
        system_prompt = self._build_system_prompt(alarm)
        tool_config = self._registry.get_bedrock_config()

        messages = [
            {
                "role": "user",
                "content": [
                    {"text": "Please investigate this alarm and provide a root cause analysis."}
                ],
            }
        ]

        for iteration in range(self._max_iterations):
            response = self._client.converse(
                modelId=self.MODEL_ID,
                system=[{"text": system_prompt}],
                messages=messages,
                toolConfig=tool_config if tool_config.get("tools") else None,
            )

            stop_reason = response.get("stopReason")
            assistant_message = response["output"]["message"]
            messages.append(assistant_message)

            if stop_reason == "end_turn":
                # Extract text from response
                for content in assistant_message["content"]:
                    if "text" in content:
                        return content["text"]
                return "Investigation complete but no report generated."

            if stop_reason == "tool_use":
                # Execute requested tools
                tool_results = []
                for content in assistant_message["content"]:
                    if "toolUse" in content:
                        tool_use = content["toolUse"]
                        tool = self._registry.get(tool_use["name"])

                        if tool:
                            result = tool.execute(**tool_use["input"])
                        else:
                            result = {"error": f"Unknown tool: {tool_use['name']}"}

                        tool_results.append(
                            {
                                "toolResult": {
                                    "toolUseId": tool_use["toolUseId"],
                                    "content": [{"json": result}],
                                }
                            }
                        )

                messages.append({"role": "user", "content": tool_results})

        return "Investigation reached max iterations. Partial analysis may be available above."
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add src/alarm_investigator/agent.py tests/test_agent.py
git commit -m "feat: add InvestigationAgent with Bedrock tool use loop"
```

---

## Task 10: Report Formatter

**Files:**
- Create: `src/alarm_investigator/output.py`
- Create: `tests/test_output.py`

**Step 1: Write the failing test**

```python
"""Tests for output formatting."""

import pytest

from alarm_investigator.models import AlarmEvent, AlarmState
from alarm_investigator.output import ReportFormatter


class TestReportFormatter:
    """Tests for ReportFormatter."""

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

    def test_format_email_report(self):
        """Test formatting report for email."""
        alarm = self.create_alarm_event()
        analysis = """## Summary
High CPU utilization on instance i-1234567890abcdef0.

## Root Cause
Application processing spike due to batch job."""

        formatter = ReportFormatter()
        result = formatter.format_email(alarm, analysis)

        assert "HighCPU" in result["subject"]
        assert "ALARM" in result["subject"]
        assert "High CPU utilization" in result["body"]
        assert "Root Cause" in result["body"]
        assert result["content_type"] == "text/html"

    def test_format_email_includes_alarm_metadata(self):
        """Test email includes alarm metadata."""
        alarm = self.create_alarm_event()
        analysis = "Test analysis"

        formatter = ReportFormatter()
        result = formatter.format_email(alarm, analysis)

        assert "123456789012" in result["body"]
        assert "us-east-1" in result["body"]
        assert "i-1234567890abcdef0" in result["body"]

    def test_format_json_report(self):
        """Test formatting report as JSON."""
        alarm = self.create_alarm_event()
        analysis = "Test analysis"

        formatter = ReportFormatter()
        result = formatter.format_json(alarm, analysis)

        assert result["alarm_name"] == "HighCPU"
        assert result["state"] == "ALARM"
        assert result["analysis"] == "Test analysis"
        assert "timestamp" in result
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_output.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
"""Report formatting for investigation output."""

import html
from datetime import datetime, timezone

from alarm_investigator.models import AlarmEvent


class ReportFormatter:
    """Formats investigation reports for various outputs."""

    def format_email(self, alarm: AlarmEvent, analysis: str) -> dict:
        """Format report for email delivery."""
        subject = f"[{alarm.state.value}] Alarm Investigation: {alarm.alarm_name}"

        # Convert markdown to basic HTML
        html_analysis = self._markdown_to_html(analysis)

        body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #f44336; color: white; padding: 20px; }}
        .header.ok {{ background: #4CAF50; }}
        .content {{ padding: 20px; }}
        .metadata {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .metadata dt {{ font-weight: bold; }}
        h2 {{ color: #1976D2; border-bottom: 2px solid #1976D2; padding-bottom: 5px; }}
        pre {{ background: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header{' ok' if alarm.state.value == 'OK' else ''}">
        <h1>🔔 Alarm Investigation Report</h1>
        <p>{html.escape(alarm.alarm_name)}</p>
    </div>
    <div class="content">
        <div class="metadata">
            <dl>
                <dt>Account</dt><dd>{html.escape(alarm.account_id)}</dd>
                <dt>Region</dt><dd>{html.escape(alarm.region)}</dd>
                <dt>State</dt><dd>{html.escape(alarm.state.value)} (was {html.escape(alarm.previous_state.value)})</dd>
                <dt>Metric</dt><dd>{html.escape(alarm.namespace or 'N/A')} / {html.escape(alarm.metric_name or 'N/A')}</dd>
                <dt>Dimensions</dt><dd>{html.escape(str(alarm.dimensions or {}))}</dd>
                <dt>Reason</dt><dd>{html.escape(alarm.reason)}</dd>
            </dl>
        </div>
        <div class="analysis">
            {html_analysis}
        </div>
    </div>
</body>
</html>
"""

        return {
            "subject": subject,
            "body": body,
            "content_type": "text/html",
        }

    def format_json(self, alarm: AlarmEvent, analysis: str) -> dict:
        """Format report as JSON."""
        return {
            "alarm_name": alarm.alarm_name,
            "account_id": alarm.account_id,
            "region": alarm.region,
            "state": alarm.state.value,
            "previous_state": alarm.previous_state.value,
            "reason": alarm.reason,
            "namespace": alarm.namespace,
            "metric_name": alarm.metric_name,
            "dimensions": alarm.dimensions,
            "analysis": analysis,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _markdown_to_html(self, text: str) -> str:
        """Simple markdown to HTML conversion."""
        lines = text.split("\n")
        html_lines = []

        for line in lines:
            if line.startswith("## "):
                html_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{html.escape(line[4:])}</h3>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{html.escape(line[2:])}</li>")
            elif line.startswith("**") and line.endswith("**"):
                html_lines.append(f"<strong>{html.escape(line[2:-2])}</strong>")
            elif line.strip():
                html_lines.append(f"<p>{html.escape(line)}</p>")

        return "\n".join(html_lines)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_output.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add src/alarm_investigator/output.py tests/test_output.py
git commit -m "feat: add ReportFormatter for email and JSON output"
```

---

## Task 11: Lambda Handler

**Files:**
- Modify: `src/alarm_investigator/handler.py`
- Create: `tests/test_handler.py`

**Step 1: Write the failing test**

```python
"""Tests for Lambda handler."""

import json
from unittest.mock import MagicMock, patch

import pytest

from alarm_investigator.handler import lambda_handler


class TestLambdaHandler:
    """Tests for Lambda handler."""

    def create_eventbridge_event(self) -> dict:
        """Create a test EventBridge event."""
        return {
            "version": "0",
            "id": "event-123",
            "detail-type": "CloudWatch Alarm State Change",
            "source": "aws.cloudwatch",
            "account": "123456789012",
            "time": "2026-01-29T10:00:00Z",
            "region": "us-east-1",
            "resources": ["arn:aws:cloudwatch:us-east-1:123456789012:alarm:HighCPU"],
            "detail": {
                "alarmName": "HighCPU",
                "state": {
                    "value": "ALARM",
                    "reason": "Threshold Crossed",
                    "timestamp": "2026-01-29T10:00:00.000+0000",
                },
                "previousState": {
                    "value": "OK",
                    "reason": "All good",
                    "timestamp": "2026-01-29T09:00:00.000+0000",
                },
                "configuration": {
                    "metrics": [
                        {
                            "id": "m1",
                            "metricStat": {
                                "metric": {
                                    "namespace": "AWS/EC2",
                                    "name": "CPUUtilization",
                                    "dimensions": {"InstanceId": "i-1234567890abcdef0"},
                                },
                                "period": 300,
                                "stat": "Average",
                            },
                            "returnData": True,
                        }
                    ]
                },
            },
        }

    @patch("alarm_investigator.handler.boto3")
    def test_handler_processes_alarm_event(self, mock_boto3):
        """Test handler processes alarm event successfully."""
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "## Analysis\nRoot cause identified."}],
                }
            },
        }

        mock_sns = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = {"Reservations": []}

        def get_client(service, **kwargs):
            clients = {
                "bedrock-runtime": mock_bedrock,
                "sns": mock_sns,
                "cloudwatch": mock_cloudwatch,
                "ec2": mock_ec2,
            }
            return clients.get(service, MagicMock())

        mock_boto3.client.side_effect = get_client

        event = self.create_eventbridge_event()
        result = lambda_handler(event, None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["alarm_name"] == "HighCPU"
        assert "analysis" in body

    @patch("alarm_investigator.handler.boto3")
    def test_handler_sends_sns_notification(self, mock_boto3):
        """Test handler sends SNS notification when topic configured."""
        mock_bedrock = MagicMock()
        mock_bedrock.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Analysis complete."}],
                }
            },
        }

        mock_sns = MagicMock()
        mock_cloudwatch = MagicMock()

        def get_client(service, **kwargs):
            clients = {
                "bedrock-runtime": mock_bedrock,
                "sns": mock_sns,
                "cloudwatch": mock_cloudwatch,
            }
            return clients.get(service, MagicMock())

        mock_boto3.client.side_effect = get_client

        with patch.dict("os.environ", {"SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:alerts"}):
            event = self.create_eventbridge_event()
            lambda_handler(event, None)

        mock_sns.publish.assert_called_once()

    @patch("alarm_investigator.handler.boto3")
    def test_handler_returns_error_on_invalid_event(self, mock_boto3):
        """Test handler returns error for invalid events."""
        event = {"invalid": "event"}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert "error" in body
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_handler.py -v`
Expected: FAIL (tests should fail because handler not implemented)

**Step 3: Write the implementation**

```python
"""Lambda handler for Alarm Investigator."""

import json
import os

import boto3

from alarm_investigator.agent import InvestigationAgent
from alarm_investigator.models import AlarmEvent
from alarm_investigator.output import ReportFormatter
from alarm_investigator.tools.base import ToolRegistry
from alarm_investigator.tools.cloudwatch import GetMetricsTool
from alarm_investigator.tools.ec2 import DescribeEC2InstanceTool
from alarm_investigator.tools.ecs import DescribeECSServiceTool
from alarm_investigator.tools.lambda_ import DescribeLambdaFunctionTool
from alarm_investigator.tools.rds import DescribeRDSInstanceTool


def lambda_handler(event: dict, context) -> dict:
    """Main Lambda entry point."""
    try:
        # Parse the alarm event
        alarm = AlarmEvent.from_eventbridge(event)
    except ValueError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": str(e)}),
        }

    # Initialize AWS clients
    region = alarm.region
    bedrock_client = boto3.client("bedrock-runtime", region_name=region)
    cloudwatch_client = boto3.client("cloudwatch", region_name=region)
    ec2_client = boto3.client("ec2", region_name=region)
    rds_client = boto3.client("rds", region_name=region)
    lambda_client = boto3.client("lambda", region_name=region)
    ecs_client = boto3.client("ecs", region_name=region)

    # Register tools
    registry = ToolRegistry()
    registry.register(GetMetricsTool(cloudwatch_client=cloudwatch_client))
    registry.register(DescribeEC2InstanceTool(ec2_client=ec2_client))
    registry.register(DescribeRDSInstanceTool(rds_client=rds_client))
    registry.register(DescribeLambdaFunctionTool(lambda_client=lambda_client))
    registry.register(DescribeECSServiceTool(ecs_client=ecs_client))

    # Run investigation
    agent = InvestigationAgent(bedrock_client=bedrock_client, tool_registry=registry)
    analysis = agent.investigate(alarm)

    # Format output
    formatter = ReportFormatter()
    report = formatter.format_json(alarm, analysis)

    # Send SNS notification if configured
    sns_topic_arn = os.environ.get("SNS_TOPIC_ARN")
    if sns_topic_arn:
        sns_client = boto3.client("sns", region_name=region)
        email_report = formatter.format_email(alarm, analysis)
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject=email_report["subject"][:100],  # SNS subject limit
            Message=email_report["body"],
        )

    return {
        "statusCode": 200,
        "body": json.dumps(report),
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_handler.py -v`
Expected: PASS (3 tests)

**Step 5: Run all tests**

Run: `pytest -v`
Expected: All tests pass

**Step 6: Commit**

```bash
git add src/alarm_investigator/handler.py tests/test_handler.py
git commit -m "feat: add Lambda handler with full investigation flow"
```

---

## Task 12: Terraform Infrastructure

**Files:**
- Create: `infrastructure/terraform/main.tf`
- Create: `infrastructure/terraform/variables.tf`
- Create: `infrastructure/terraform/outputs.tf`

**Step 1: Create infrastructure directory**

```bash
mkdir -p infrastructure/terraform
```

**Step 2: Create variables.tf**

```hcl
variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "notification_email" {
  description = "Email address to receive alarm investigation reports"
  type        = string
}
```

**Step 3: Create main.tf**

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  function_name = "alarm-investigator-${var.environment}"
}

# SNS Topic for notifications
resource "aws_sns_topic" "alarm_reports" {
  name = "${local.function_name}-reports"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alarm_reports.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${local.function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.function_name}-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:Converse"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricData",
          "cloudwatch:DescribeAlarms"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeVolumes"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:GetFunction"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:DescribeTasks",
          "ecs:DescribeClusters"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.alarm_reports.arn
      }
    ]
  })
}

# Lambda function
resource "aws_lambda_function" "alarm_investigator" {
  function_name = local.function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "alarm_investigator.handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 300
  memory_size   = 512

  filename         = "${path.module}/../../dist/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/../../dist/lambda.zip")

  environment {
    variables = {
      SNS_TOPIC_ARN = aws_sns_topic.alarm_reports.arn
    }
  }

  architectures = ["arm64"]
}

# EventBridge Rule to trigger on CloudWatch Alarms
resource "aws_cloudwatch_event_rule" "alarm_state_change" {
  name        = "${local.function_name}-trigger"
  description = "Trigger alarm investigator on CloudWatch alarm state changes"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      state = {
        value = ["ALARM"]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.alarm_state_change.name
  target_id = "InvokeAlarmInvestigator"
  arn       = aws_lambda_function.alarm_investigator.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.alarm_investigator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.alarm_state_change.arn
}
```

**Step 4: Create outputs.tf**

```hcl
output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.alarm_investigator.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.alarm_investigator.arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for reports"
  value       = aws_sns_topic.alarm_reports.arn
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.alarm_state_change.name
}
```

**Step 5: Commit**

```bash
git add infrastructure/terraform/
git commit -m "feat: add Terraform infrastructure for Lambda deployment"
```

---

## Task 13: Build Script and README

**Files:**
- Create: `scripts/build.sh`
- Create: `README.md`

**Step 1: Create scripts directory and build script**

```bash
mkdir -p scripts
```

**Step 2: Create scripts/build.sh**

```bash
#!/bin/bash
set -e

echo "Building Alarm Investigator Lambda package..."

# Clean previous build
rm -rf dist/
mkdir -p dist/package

# Install dependencies
pip install -r requirements.txt -t dist/package/

# Copy source code
cp -r src/alarm_investigator dist/package/

# Create zip
cd dist/package
zip -r ../lambda.zip .
cd ../..

echo "Build complete: dist/lambda.zip"
ls -lh dist/lambda.zip
```

**Step 3: Make build script executable**

```bash
chmod +x scripts/build.sh
```

**Step 4: Create README.md**

```markdown
# 🔍 Alarm Investigator (AI)

AI-powered CloudWatch alarm investigation agent. Automatically analyzes alarms using Claude on Amazon Bedrock to identify root causes and provide actionable insights.

## Features

- 🤖 **AI-Powered Analysis** - Uses Claude Sonnet on Bedrock for intelligent investigation
- 🔧 **Multi-Service Support** - Investigates EC2, RDS, Lambda, ECS resources
- 📊 **Metric Analysis** - Retrieves and analyzes CloudWatch metrics
- 📧 **Email Reports** - Sends detailed reports via SNS
- ⚡ **Event-Driven** - Triggers automatically on CloudWatch alarm state changes
- 🏗️ **Infrastructure as Code** - Deploy with Terraform

## Quick Start

### Prerequisites

- Python 3.12+
- AWS CLI configured
- Terraform 1.0+
- Access to Amazon Bedrock (Claude Sonnet model enabled)

### Installation

```bash
# Clone the repository
git clone https://github.com/ferdinandobons/alarm-investigator.git
cd alarm-investigator

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

### Deploy

```bash
# Build Lambda package
./scripts/build.sh

# Deploy with Terraform
cd infrastructure/terraform
terraform init
terraform apply -var="notification_email=your@email.com"
```

### Test

Trigger a CloudWatch alarm or manually invoke the Lambda:

```bash
aws lambda invoke \
  --function-name alarm-investigator-dev \
  --payload file://examples/test-event.json \
  response.json
```

## Architecture

```
CloudWatch Alarm → EventBridge → Lambda → Bedrock (Claude)
                                    ↓
                              AWS APIs (EC2, RDS, etc.)
                                    ↓
                              SNS Email Report
```

## Configuration

| Environment Variable | Description | Required |
|---------------------|-------------|----------|
| `SNS_TOPIC_ARN` | SNS topic for email reports | No |

## Supported Services

| Service | Investigation Capabilities |
|---------|---------------------------|
| EC2 | Instance details, state, network config |
| RDS | DB instance status, config, Multi-AZ |
| Lambda | Function config, memory, timeout |
| ECS | Service status, task counts, deployments |
| CloudWatch | Metric data retrieval and analysis |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/ tests/

# Format code
ruff format src/ tests/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
```

**Step 5: Create example test event**

```bash
mkdir -p examples
```

Create `examples/test-event.json`:

```json
{
  "version": "0",
  "id": "test-event-123",
  "detail-type": "CloudWatch Alarm State Change",
  "source": "aws.cloudwatch",
  "account": "123456789012",
  "time": "2026-01-29T10:00:00Z",
  "region": "us-east-1",
  "resources": ["arn:aws:cloudwatch:us-east-1:123456789012:alarm:TestAlarm"],
  "detail": {
    "alarmName": "TestAlarm",
    "state": {
      "value": "ALARM",
      "reason": "Threshold Crossed: 1 datapoint (85.0) was greater than the threshold (80.0)",
      "timestamp": "2026-01-29T10:00:00.000+0000"
    },
    "previousState": {
      "value": "OK",
      "reason": "Threshold not crossed",
      "timestamp": "2026-01-29T09:00:00.000+0000"
    },
    "configuration": {
      "metrics": [
        {
          "id": "m1",
          "metricStat": {
            "metric": {
              "namespace": "AWS/EC2",
              "name": "CPUUtilization",
              "dimensions": {
                "InstanceId": "i-1234567890abcdef0"
              }
            },
            "period": 300,
            "stat": "Average"
          },
          "returnData": true
        }
      ]
    }
  }
}
```

**Step 6: Commit**

```bash
git add scripts/ README.md examples/
git commit -m "docs: add README, build script, and example event"
```

---

## Task 14: Final Verification and Push

**Step 1: Run all tests**

Run: `pytest -v --cov=alarm_investigator`
Expected: All tests pass with good coverage

**Step 2: Run linter**

Run: `ruff check src/ tests/`
Expected: No errors

**Step 3: Build package**

Run: `./scripts/build.sh`
Expected: `dist/lambda.zip` created

**Step 4: Push to GitHub**

```bash
git push origin main
```

---

## Summary

This plan implements the Phase 1 MVP with:

- ✅ Alarm event parsing from EventBridge
- ✅ Tool framework for AWS service investigation
- ✅ 5 investigation tools (CloudWatch, EC2, RDS, Lambda, ECS)
- ✅ Bedrock agent orchestrator with tool use loop
- ✅ Report formatting (email HTML, JSON)
- ✅ Lambda handler with full flow
- ✅ Terraform infrastructure
- ✅ Tests for all components
- ✅ Documentation and examples
