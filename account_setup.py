import boto3
from botocore.exceptions import ClientError
import json
import os
import sys
import time
import zipfile

#Sets up our boto3 clients
iamClient = boto3.client('iam')
eventsClient = boto3.client('events')
lambdaClient = boto3.client('lambda')

#This is the policy we'll attach to the role
policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "logs:*",
                "lambda:*"
            ],
            "Effect": "Allow",
            "Resource": "*"
        }
    ]
}

#The role service document
role_document= {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}

def zip_function():
  """
  Zips up our function into a package to be uploaded
  """
  output_path = os.getcwd() + '/dist.zip'
  folder_path = os.curdir + '/dist'
  grab_lambda = os.walk(folder_path)
  length = len(folder_path)

  try:
    zipped_lambda = zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED)
    for root, folders, files in grab_lambda:
      for folder_name in folders:
        absolute_path = os.path.join(root, folder_name)
        shortened_path = os.path.join(root[length:], folder_name)
        print("Adding '%s' to package." % shortened_path)
        zipped_lambda.write(absolute_path, shortened_path)
      for file_name in files:
        absolute_path = os.path.join(root, file_name)
        shortened_path = os.path.join(root[length:], file_name)
        print("Adding '%s' to package." % shortened_path)
        zipped_lambda.write(absolute_path, shortened_path)
    print("lambda packaged successfully.")
    return True
  except IOError:
    print(message)
    sys.exit(1)
  except OSError:
    print(message)
    sys.exit(1)
  except zipfile.BadZipfile:
    print(message)
    sys.exit(1)
  finally:
    zipped_lambda.close()

class LambdaRole(object):
    def __init__(self, role_document, policy_document):
        self.role_document = role_document
        self. policy_document = policy_document

    def create_role(self):
        """
        Creates a role 
        """
        print("Creating role")
        try:
            create_role = iamClient.create_role(
                                                Path='/',
                                                RoleName='cloudwatch-cleanup-role',
                                                AssumeRolePolicyDocument=json.dumps(self.role_document),
                                                Description='IAM role for CloudWatch Cleanup Lambda'
                                            )
        except ClientError as error:
            print(error.response)
        finally:
            print("Role created")
            return create_role['Role']['Arn'], create_role['Role']['RoleName']

    def create_policy(self):
        """
        Creates a policy for the above role
        """
        print("Creating policy")
        try:
            create_policy = iamClient.create_policy(
                                                Path='/',
                                                PolicyName='cloudwatch-cleanup-lambda-policy',
                                                PolicyDocument=json.dumps(self.policy_document),
                                                Description='IAM policy for Cloudwatch Cleanup Lambda Role'
                                            )
        except ClientError as error:
            print(error.response)
        finally:
            print("Policy created")
            return create_policy['Policy']['Arn']

    def attach_policy(self, role_name, policy_arn):
        """
        Attaches policy to role
        """
        print("Attaching role to policy")
        try:
            attach_policy = iamClient.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
        except ClientError as error:
            print(error.response)
        finally:
            if attach_policy['ResponseMetadata']['HTTPStatusCode'] == 200:
                print("Policy attached successfully")
                return True
            else:
                return False

class CloudWatchEvent(object):
    def __init__(self, rule_name, rate):
        self.rule_name = rule_name
        self.rate = rate

    def create_cloudwatch_rule(self):
        """
        Creates cloudwatch rule
        """
        print("Creating cloudwatch rule %s" % self.rule_name)
        try:
            create_rule = eventsClient.put_rule(
                                            Name=self.rule_name,
                                            ScheduleExpression="rate(%s)" % self.rate,
                                            State="ENABLED",
                                            Description="Event rule to trigger Cloudwatch Cleanup Lambda every %s" % self.rate
                                                )
        except ClientError as error:
            print(error.response)
        finally:
            return create_rule['RuleArn']

    def put_rule_policy(self, lambda_name, lambda_arn):
        """
        Adds our lambda as the rule policy
        """
        print("Adding target to CloudWatch rule")
        try:
            put_policy = eventsClient.put_targets(
                                            Rule=self.rule_name,
                                            Targets=[{
                                                'Id': lambda_name,
                                                'Arn': lambda_arn
                                                }]
                                            )
        except ClientError as error:
            print(error)
        finally:
            if put_policy['FailedEntryCount'] == 0:
                print("Event target added successfully")
                return True

class Lambda(object):
    def __init__(self, lambda_name, role_arn):
        self.lambda_name = lambda_name
        self.role_arn = role_arn

    def create(self):
        """
        Creates the lambda
        """
        print("Attempting to create lambda")
        try:
            create_lambda = lambdaClient.create_function(
                                                FunctionName=self.lambda_name,
                                                Runtime='python3.6',
                                                Role=self.role_arn,
                                                Handler='main.handler',
                                                Code={
                                                    'ZipFile': open('dist.zip', 'rb').read()
                                                },
                                                Description='CloudWatch Logs Cleanup Lambda',
                                                Timeout=30,
                                                MemorySize=128,
                                                Tags={
                                                    "Name": "cloudWatch-logs-manager"
                                                }
                                            )
        except ClientError as error:
            print(error.response)
        finally:
            print("Lambda created successfully")
            return create_lambda['FunctionArn']

    def add_invoke_permission(self, source_arn):
        """
        Adds permission for the cloudwatch rule
        """
        print("Adding event permission to lambda")
        try:
            add_perms = lambdaClient.add_permission(
                                                FunctionName=self.lambda_name,
                                                StatementId='cloudwatch-event-trigger-lambda',
                                                Action='lambda:InvokeFunction',
                                                Principal='events.amazonaws.com',
                                                SourceArn=source_arn
                                                )
        except ClientError as error:
            print(error.response)
        finally:
            if add_perms['ResponseMetadata']['HTTPStatusCode'] == 200:
                print("Permission addedd successfully")
                return True

def main():
    """
    The below variables can be changed to whatever you see fit.

    If you are going to update the run rate it should remain in the format 'X days' or 'X mins'
    """
    LAMBDA_NAME = 'cloudwatch-logs-manager-lambda'
    RULE_NAME = 'Cloudwatch-Cleanup-Rule'
    RUN_RATE = '14 days'

    """
    Starts us off by zipping the function
    """
    zip_function()

    #Creates a role
    role_object = LambdaRole(role_document, policy_document)
    role_arn, role_name = role_object.create_role()
    policy_arn = role_object.create_policy()
    attach = role_object.attach_policy(role_name, policy_arn)
    
    print("Sleeping for 10 seconds")
    time.sleep(10)

    #Create the lambda
    lambda_object = Lambda(LAMBDA_NAME, role_arn)
    lambda_arn = lambda_object.create()

    #Create the rule
    event_object = CloudWatchEvent(rule_name=RULE_NAME, rate=RUN_RATE)
    event_rule_arn = event_object.create_cloudwatch_rule()

    #Policies
    add_invoke_perms = lambda_object.add_invoke_permission(event_rule_arn)
    add_event_target = event_object.put_rule_policy(LAMBDA_NAME, lambda_arn)

if __name__ == '__main__':
    main()
