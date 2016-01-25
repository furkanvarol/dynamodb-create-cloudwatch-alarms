#!/usr/bin/env python
"""dynamodb-create-cloudwatch-alarms

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
"""

import boto
import boto.ec2
import boto.dynamodb
from docopt import docopt
from boto.ec2.cloudwatch import MetricAlarm
from schema import Schema, And, Use, SchemaError

DEBUG = False

DDB_METRICS = frozenset([u'ConsumedReadCapacityUnits', u'ConsumedWriteCapacityUnits'])

PREFIX = None
SNS = None
RATIO = 0.8
REGION = 'us-east-1'
ALARM_PERIOD = 300
EVALUATION_PERIOD = 12


def get_ddb_tables():
    """
    Retrieves all DynamoDB table names (which starts with PREFIX if supplied)

    Returns:
        (set) Of valid DynamoDB table names
    """

    ddb_connection = boto.dynamodb.connect_to_region(REGION)
    ddb_tables_list = ddb_connection.list_tables()
    ddb_tables = set()
    for ddb_table in ddb_tables_list:

        # checking whether a prefix given and matches with table name
        if PREFIX and not ddb_table.startswith(PREFIX):
            continue

        ddb_table_attributes = ddb_connection.describe_table(ddb_table)
        # creating a variable for each unit to satisfy flake8
        ddb_tablename = ddb_table_attributes[u'Table'][u'TableName']
        ddb_rcu = (ddb_table_attributes
                   [u'Table'][u'ProvisionedThroughput'][u'ReadCapacityUnits'])
        ddb_wcu = (ddb_table_attributes
                   [u'Table'][u'ProvisionedThroughput'][u'WriteCapacityUnits'])
        ddb_tables.add((ddb_tablename, ddb_rcu, ddb_wcu))

    return ddb_tables


def get_existing_alarm_names(aws_cw_connect):
    """
    Retrieves all DynamoDB related CloudWatch alarm names

    Args:
        aws_cw_connect (CloudWatchConnection)

    Returns:
        (dict) Existing CloudWatch DDB alarms (name and threshold)
    """

    assert isinstance(aws_cw_connect,
                      boto.ec2.cloudwatch.CloudWatchConnection)

    page_loop = aws_cw_connect.describe_alarms()
    existing_alarms = set()

    # adding the 1st page of alarms
    for alarm in page_loop:
        existing_alarms.add(alarm)

    while page_loop.next_token:
        page_loop = (aws_cw_connect.
                     describe_alarms(next_token=page_loop.next_token))
        # appending the latter pages
        for alarm in page_loop:
            existing_alarms.add(alarm)

    existing_alarm_names = {}

    for existing_alarm in existing_alarms:
        if existing_alarm.namespace == u'AWS/DynamoDB':
            existing_alarm_names.update({existing_alarm.name:
                                         existing_alarm.threshold})

    return existing_alarm_names


def get_ddb_alarms_to_create(ddb_tables, aws_cw_connect):
    """
    Creates a Read/Write Capacity Units alarm
    for all DynamoDB tables

    Args:
        ddb_tables (set) ist of all DynamoDB tables
        aws_cw_connect (CloudWatchConnection)

    Returns:
        (set) All new Read/Write Capacity Units alarms that'll be created
        (set) All existing Read/Write Capacity Units alarms that'll be updated
    """

    assert isinstance(ddb_tables, set)
    assert isinstance(aws_cw_connect,
                      boto.ec2.cloudwatch.CloudWatchConnection)

    alarms_to_create = set()
    alarms_to_update = set()
    existing_alarms = get_existing_alarm_names(aws_cw_connect)

    for table in ddb_tables:
        # we want two alarms per DynamoDB table
        for metric in DDB_METRICS:
            if metric == u'ConsumedReadCapacityUnits':
                threshold = table[1]
            elif metric == u'ConsumedWriteCapacityUnits':
                threshold = table[2]

            # initiate a MetricAlarm object for each DynamoDb table.
            # for the threshold we calculate the 80 percent
            # from the tables ProvisionedThroughput values
            ddb_table_alarm = MetricAlarm(
                name=u'{}-{}-BasicAlarm'.format(
                    table[0],
                    metric.replace('Consumed','') + 'Limit'
                ),
                namespace=u'AWS/DynamoDB',
                metric=u'{}'.format(metric), statistic='Sum',
                comparison=u'>=',
                threshold=RATIO*threshold*ALARM_PERIOD,
                period=ALARM_PERIOD,
                evaluation_periods=EVALUATION_PERIOD,
                # Below insert the actions appropriate.
                alarm_actions=[SNS],
                dimensions={u'TableName': table[0]}
            )

            # we create an Alarm metric for each new DDB table
            if ddb_table_alarm.name not in existing_alarms.iterkeys():
                alarms_to_create.add(ddb_table_alarm)

            # checking the existing alarms thresholds
            # update them if there are changes
            for key, value in existing_alarms.iteritems():
                if (key == ddb_table_alarm.name
                        and value != ddb_table_alarm.threshold):
                    alarms_to_update.add(ddb_table_alarm)

    return (alarms_to_create, alarms_to_update)


def main():
    args = docopt(__doc__)

    # validating arguments
    schema = Schema({
        '-r': And(Use(int), lambda n: 10 <= n <= 95,
                      error='-r must be integer and 10 <= N <= 95'),
        '-R': And(boto.ec2.get_region,
                      error='-R must be a valid region name'),
        '-a': And(Use(int), lambda s: s >= 60,
                      error='-a must be integer and S >= 60'),
        '-e': And(Use(int), lambda n: n >= 1,
                      error='-e must be integer and N >= 1'),
        str: object})

    try:
        args = schema.validate(args)
    except SchemaError as e:
        exit(e)

    # setting arguments
    global DEBUG, RATIO, REGION, SNS, PREFIX, ALARM_PERIOD, EVALUATION_PERIOD

    DEBUG = args['-d']
    RATIO = args['-r'] / 100.0
    REGION = args['-R']
    SNS = args['-s']
    PREFIX = args['-p']
    ALARM_PERIOD = args['-a']
    EVALUATION_PERIOD = args['-e']

    ddb_tables = get_ddb_tables()
    aws_cw_connect = boto.ec2.cloudwatch.connect_to_region(REGION)

    (alarms_to_create,
     alarms_to_update) = get_ddb_alarms_to_create(ddb_tables, aws_cw_connect)

    # creating new alarms
    if alarms_to_create:
        if DEBUG:
            for alarm in alarms_to_create:
                print 'DEBUG CREATED:', alarm
        else:
            print 'New DynamoDB table(s) Alarms created:'
            for alarm in alarms_to_create:
                aws_cw_connect.create_alarm(alarm)
                print alarm

    # updating existing alarms
    if alarms_to_update:
        if DEBUG:
            for alarm in alarms_to_update:
                print 'DEBUG UPDATED:', alarm
        else:
            print 'DynamoDB table(s) Alarms updated:'
            for alarm in alarms_to_update:
                aws_cw_connect.update_alarm(alarm)
                print alarm

if __name__ == '__main__':
    main()
