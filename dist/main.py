import boto3
from botocore.exceptions import ClientError
import json
import os
import sys

logsClient = boto3.client('logs')
expiration = 120

def get_groups():
    log_groups = []

    try:
        get_logs = logsClient.describe_log_groups()

        if len(get_logs['logGroups']) != 0:
            for group in get_logs['logGroups']:
                log_groups.append(group['logGroupName'])
    except ClientError as error:
        print(error.response)
    finally:
        return log_groups

def get_retention_policy(groups, expiration):
    groups_to_update = []

    for group in groups:
        try:
            log_group = logsClient.describe_log_groups(logGroupNamePrefix=group)

            group_info = log_group['logGroups'][0]

            group_name = group_info['logGroupName']

            if 'retentionInDays' in group_info and group_info['retentionInDays'] == expiration:
                print('Log Group: "%s" passed check' % group_name.split('/')[3])
            else:
                groups_to_update.append(group_info['logGroupName'])
        except ClientError as error:
            print(error.response)

    return groups_to_update

def put_group_policy(groups, expiration):
    for group in groups:
        try:
            update_policy = logsClient.put_retention_policy(logGroupName=group, retentionInDays=expiration)
        except ClientError as error:
            print(error.response)
        finally:
            print('Updated groups %s with a policy of %s days' % (group, expiration))
            
def handler(event, context):
    groups = get_groups()
    groups_to_update = get_retention_policy(groups=groups, expiration=expiration)
    update_groups = put_group_policy(groups=groups_to_update, expiration=expiration)