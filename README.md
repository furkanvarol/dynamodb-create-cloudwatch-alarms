# dynamodb-create-cloudwatch-alarms

[![Circle CI](https://circleci.com/gh/percolate/dynamodb-create-cloudwatch-alarms.svg?style=svg)](https://circleci.com/gh/percolate/dynamodb-create-cloudwatch-alarms)

Automate the creation of DynamoDB ProvisionedThroughput Read/Write Alarms.
The `ProvisionedThroughput` upper-bound limit in the script is 80%, but this can be altered.

# Quick Start
```bash
$ dynamodb_create_cloudwatch_alarms --help

Script used to create above 80% Read/Write Capacity Units
AWS CloudWatch alarms for each DynamoDB table.
If set as a cron job - updates existing alarms if
Read/Write Capacity Units DynamoDB table parameters changed.

Usage:
    dynamodb-create-cloudwatch-alarms (--sns <sns_topic_arn>) [options
    dynamodb_create_cloudwatch_alarms [-h | --help]

Options:
    -h,    --help                 Show this screen and exit.
    -d,    --debug                Don't send data to AWS.
    -s=S,  --sns=S                AWS SNS TOPIC (required)
    -r=N,  --ratio=N              Upper bound limit between 10 and 95 (inclusive) [default: 80].
    -ap=S, --alarm-period=S       Sets alarm period in seconds [default: 300]
    -ep=N, --evaluation-period=N  Sets alarm evalutation period (consecutive) [default: 12]
    -r=R,  --region=R             Region name to connect AWS [default: us-east-1].

Examples:
    dynamodb_create_cloudwatch_alarms --sns=TOPIC
    dynamodb_create_cloudwatch_alarms --sns=TOPIC --debug
    dynamodb_create_cloudwatch_alarms --sns=TOPIC --ratio=90
    dynamodb_create_cloudwatch_alarms --sns=TOPIC --region=eu-west-1
    dynamodb_create_cloudwatch_alarms --sns=TOPIC --ratio=90 --region=eu-west-1
    dynamodb_create_cloudwatch_alarms --sns=TOPIC --debug --ratio=90 --region=eu-west-1
```

# Install
```bash
$ pip install dynamodb_create_cloudwatch_alarms
```
