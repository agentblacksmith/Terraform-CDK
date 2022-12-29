#!/usr/bin/env python
import os
from constructs import Construct
from cdktf import App, TerraformStack, RemoteBackend, NamedRemoteWorkspace, TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.dynamodb_table import DynamodbTable
from cdktf_cdktf_provider_aws.lambda_function import LambdaFunction, LambdaFunctionEnvironment
from cdktf_cdktf_provider_aws.lambda_event_source_mapping import LambdaEventSourceMapping
from cdktf_cdktf_provider_aws.cloudwatch_log_group import CloudwatchLogGroup

# DynamoDB varialbes
DynamoDB_Table = "GameScores"
DynamoDB_Billing = "PAY_PER_REQUEST"
DynamoDB_Partion_Key = 'UserId'
DynamoDB_Sortkey = 'GameTitle'
DynamoDB_Attribute_Type = 'S'

# Lambda function vars
Lambda_Function_Name = "dynamodbStreamFunction"
Lambda_Function_Log_Group = f"/aws/lambda/{Lambda_Function_Name}"


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)
        AwsProvider(self, "AWS", region='us-east-1')

        # Cloudwatch log group creation
        cloudwatchLogGroup = CloudwatchLogGroup(
            self, "LogGroup", name=Lambda_Function_Log_Group, retention_in_days=3)

        # DynamoDB Table
        dynamodb_table = DynamodbTable(self, "dynamodb",
                                       name=DynamoDB_Table,
                                       billing_mode=DynamoDB_Billing,
                                       hash_key=DynamoDB_Partion_Key,
                                       range_key=DynamoDB_Sortkey,
                                       attribute=[
                                           {
                                             "name": DynamoDB_Partion_Key,
                                               "type": DynamoDB_Attribute_Type
                                           },
                                           {
                                               "name": DynamoDB_Sortkey,
                                               "type": DynamoDB_Attribute_Type
                                           },
                                       ],
                                       stream_enabled=True,
                                       stream_view_type="NEW_AND_OLD_IMAGES"
                                       )

        # Lambda function creation
        lambda_function = LambdaFunction(self,
                                         Lambda_Function_Name,
                                         function_name=Lambda_Function_Name,
                                         runtime="python3.8",
                                         handler="sample.handler",
                                         filename=os.path.abspath(
                                             "lambda1.zip"),
                                         role="arn:aws:iam::865227664036:role/service-role/dynamodb-opeansearch-stream-lambda-role-ocu941je",
                                         environment=LambdaFunctionEnvironment(variables={
                                             "URL": "https://example.com"
                                         }),
                                         vpc_config={
                                             "subnet_ids": ["subnet-01623eca4025f6072"],
                                             "security_group_ids": ["sg-0985519ebe26980da"]
                                         }
                                         )

        # DynamoDB Stream event source mapping
        dynamdb_stream_lambda = LambdaEventSourceMapping(self, "lambd_function_stream_trigger",
                                                               function_name     = lambda_function.function_name,
                                                               event_source_arn  = dynamodb_table.stream_arn,
                                                               starting_position = "LATEST"
                                                         )


app = App()
stack = MyStack(app, "learn-cdktf-dynamdb")
# RemoteBackend(stack,
#   hostname='app.terraform.io',
#   organization='example-org-8df812',
#   workspaces=NamedRemoteWorkspace('learn-cdktf-dynamdb')
# )

app.synth()
