# Alarm Investigator (AI)

AI-powered CloudWatch alarm investigation agent. Automatically analyzes alarms using Claude on Amazon Bedrock to identify root causes and provide actionable insights.

## Features

- **AI-Powered Analysis** - Uses Claude Sonnet on Bedrock for intelligent investigation
- **Multi-Service Support** - Investigates EC2, RDS, Lambda, ECS resources
- **Metric Analysis** - Retrieves and analyzes CloudWatch metrics
- **Email Reports** - Sends detailed reports via SNS
- **Event-Driven** - Triggers automatically on CloudWatch alarm state changes
- **Infrastructure as Code** - Deploy with Terraform

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
CloudWatch Alarm -> EventBridge -> Lambda -> Bedrock (Claude)
                                    |
                              AWS APIs (EC2, RDS, etc.)
                                    |
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
