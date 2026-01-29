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
