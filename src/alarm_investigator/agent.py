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
- **Namespace:** {alarm.namespace or "N/A"}
- **Metric:** {alarm.metric_name or "N/A"}
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
