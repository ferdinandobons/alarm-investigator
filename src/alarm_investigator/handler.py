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
