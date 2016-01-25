# dynamodb-create-cloudwatch-alarms

[![Circle CI](https://circleci.com/gh/percolate/dynamodb-create-cloudwatch-alarms.svg?style=svg)](https://circleci.com/gh/percolate/dynamodb-create-cloudwatch-alarms)

Automate the creation of DynamoDB ProvisionedThroughput Read/Write Alarms.
The `ProvisionedThroughput` upper-bound limit in the script is 80%, but this can be altered.

# Quick Start
```
$ dynamodb_create_cloudwatch_alarms --help

Script used to create above 80% Read/Write Capacity Units
AWS CloudWatch alarms for each DynamoDB table.
If set as a cron job - updates existing alarms if
Read/Write Capacity Units DynamoDB table parameters changed.

Usage:
    dynamodb-create-cloudwatch-alarms (-s <topic>) [-d] [-p <str>] [-r <n>] [-a <sec>] [-e <n>] [-R <region>]
    dynamodb-create-cloudwatch-alarms [-h | --help]

Options:
    -h, --help   Show this screen and exit.
    -d           Don't send data to AWS.
    -s <topic>   AWS SNS ARN topic (required).
    -p <str>     DynamoDB table name prefix.
    -r <n>       Upper bound limit between 10 and 95 (inclusive) [default: 80].
    -a <sec>     Sets alarm period in seconds (>= 60) [default: 300].
    -e <n>       Sets alarm evalutation period (consecutive) (>= 1) [default: 12].
    -R <region>  Region name to connect AWS [default: us-east-1].

Examples:
    dynamodb_create_cloudwatch_alarms -s arn:aws:sns:eu-west-1:123456789012:dynamodb_sns
    dynamodb_create_cloudwatch_alarms -s arn:aws:sns:eu-west-1:123456789012:dynamodb_sns -d
    dynamodb_create_cloudwatch_alarms -s arn:aws:sns:eu-west-1:123456789012:dynamodb_sns -r 90
    dynamodb_create_cloudwatch_alarms -s arn:aws:sns:eu-west-1:123456789012:dynamodb_sns -R eu-west-1
    dynamodb_create_cloudwatch_alarms -s arn:aws:sns:eu-west-1:123456789012:dynamodb_sns -r 90 -R eu-west-1
    dynamodb_create_cloudwatch_alarms -s arn:aws:sns:eu-west-1:123456789012:dynamodb_sns -p my_ddb_table
    dynamodb_create_cloudwatch_alarms -s arn:aws:sns:eu-west-1:123456789012:dynamodb_sns -a 300 -e 12
    dynamodb_create_cloudwatch_alarms -s arn:aws:sns:eu-west-1:123456789012:dynamodb_sns -r 90 -R eu-west-1 -p my_ddb_table -a 300 -e 12 -d
```

# Install
```bash
$ pip install dynamodb_create_cloudwatch_alarms
```
