import boto3
from botocore.exceptions import ClientError
import json
import os
import sys

import local_config

EXPIRATION = local_config.EXPIRATION
REGIONS = local_config.REGIONS 

class RegionGroups(object):
    def __init__(self, region):
        self.region = region

    def get_groups(self):
        logsClient = boto3.client('logs', region_name=self.region)

        log_groups = []

        try:
            get_logs = logsClient.describe_log_groups()

            if len(get_logs['logGroups']) != 0:
                for group in get_logs['logGroups']:
                    log_groups.append(group['logGroupName'])
            else:
                log_groups = None
        except ClientError as error:
            print(error.response)
        finally:
            return log_groups

    def get_retention_policy(self, groups, expiration):
        logsClient = boto3.client('logs', region_name=self.region)

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

    def put_group_policy(self, groups, expiration):
        logsClient = boto3.client('logs', region_name=self.region)

        for group in groups:
            try:
                update_policy = logsClient.put_retention_policy(logGroupName=group, retentionInDays=expiration)
            except ClientError as error:
                print(error.response)
            finally:
                print('Updated groups %s with a policy of %s days' % (group, expiration))

###### Entry #######
def handler(event, context):
    for region in REGIONS: 
        print("Checking CloudWatch Logs in " + region)
        region_groups = RegionGroups(region)

        groups = region_groups.get_groups()

        if groups != None:
            groups_to_update = region_groups.get_retention_policy(groups=groups, expiration=EXPIRATION)
            update_groups = region_groups.put_group_policy(groups=groups_to_update, expiration=EXPIRATION)
        else:
            print("No groups found")