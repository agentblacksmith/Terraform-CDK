#!/usr/bin/env python
import os
import json
from constructs import Construct
from cdktf import App, TerraformStack, RemoteBackend, NamedRemoteWorkspace, TerraformOutput
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.dynamodb_table import DynamodbTable
from cdktf_cdktf_provider_aws.lambda_function import LambdaFunction, LambdaFunctionEnvironment
from cdktf_cdktf_provider_aws.lambda_event_source_mapping import LambdaEventSourceMapping
from cdktf_cdktf_provider_aws.cloudwatch_log_group import CloudwatchLogGroup
from cdktf_cdktf_provider_aws.opensearch_domain import OpensearchDomain, OpensearchDomainDomainEndpointOptions, OpensearchDomainEbsOptions
from cdktf_cdktf_provider_aws.opensearch_domain_policy import OpensearchDomainPolicy
from cdktf_cdktf_provider_aws.iam_role import IamRole

# AWS variables
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
Account_ID = os.environ.get("ACCOUNT_ID", "865227664036")

# IAM variables
Service_role = os.environ.get("SERVICE_ROLE","dynamodb-opeansearch-stream-lambda-role-ocu941je")
Service_role_arn = f"arn:aws:iam::{Account_ID}:role/service-role/{Service_role}"

# Vpc variables
Vpc_configs_lambda = {
    "subnet_ids": ["subnet-01623eca4025f6072"],
    "security_group_ids": ["sg-0985519ebe26980da"]
}
Vpc_configs_opensearch = {
    "subnet_ids": ["subnet-01623eca4025f6072"],
    "security_group_ids": ["sg-0d62ff1ebe26cd0d5"]
}


# DynamoDB varialbes
DynamoDB_Table = "GameScores"
DynamoDB_Billing = "PAY_PER_REQUEST"
DynamoDB_Partion_Key = 'UserId'
DynamoDB_Sortkey = 'GameTitle'
DynamoDB_Attribute_Type = 'S'

# Lambda function vars
Lambda_Function_Name = "dynamodbStreamFunction"
Lambda_Function_Log_Group = f"/aws/lambda/{Lambda_Function_Name}"
Lambda_Function_Handler = "sample.handler"
Lambda_Function_Payload = "lambda-opensearch.zip"

# Opensearch variables
Opensearch_domain = "gamescores-domain"
Opensearch_version = "OpenSearch_2.3"
Opensearch_instance_type = "t3.small.search"
Opensearch_data_node_count = 1
Opnesearch_dedicated_master_count = 0
Opensearch_dedicated_master_enabled = False
Opensearch_zone_awareness_enabled = False
Opensearch_ebs_enabled = True
Opensearch_volume_size = 10
Opensearch_ttl_policy = "Policy-Min-TLS-1-2-2019-07"
Opensearch_domain_arn = f"arn:aws:es:us-east-1:{Account_ID}:domain/"
Opensearch_policy = {
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": Service_role_arn
      },
      "Action": "es:DescribeDomain,es:ESHttp*",
      "Resource": f"{Opensearch_domain_arn}{Opensearch_domain}/*"
    }
  ]
}

class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)
        AwsProvider(self, "AWS", region=AWS_REGION)

        
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

        # OpenSearch Domain creation
        opensearch_domain = OpensearchDomain(self, "opensearch_domain", domain_name=Opensearch_domain,
                                             engine_version=Opensearch_version,
                                             vpc_options=Vpc_configs_opensearch,
                                             cluster_config={
                                                 "dedicated_master_count": Opnesearch_dedicated_master_count,
                                                 "dedicated_master_enabled": Opensearch_dedicated_master_enabled,
                                                 "instance_count": Opensearch_data_node_count,
                                                 "instance_type": Opensearch_instance_type,
                                                 "zone_awareness_enabled": Opensearch_zone_awareness_enabled
                                             },
                                             access_policies=json.dumps(Opensearch_policy),
                                             domain_endpoint_options=OpensearchDomainDomainEndpointOptions(
                                                 enforce_https=True,
                                                 tls_security_policy=Opensearch_ttl_policy),
                                             ebs_options=OpensearchDomainEbsOptions(
                                                 ebs_enabled=Opensearch_ebs_enabled, volume_size=Opensearch_volume_size)
                                            
                                             )


        # Lambda function creation
        lambda_function=LambdaFunction(self,
                                         Lambda_Function_Name,
                                         function_name=Lambda_Function_Name,
                                         runtime="python3.8",
                                         handler=Lambda_Function_Handler,
                                         filename=os.path.abspath(
                                             Lambda_Function_Payload),
                                         role=Service_role_arn,
                                         environment=LambdaFunctionEnvironment(variables={
                                             "ENDPOINT": f"https://{opensearch_domain.endpoint}"
                                         }),
                                         publish=True,
                                         depends_on=[opensearch_domain],
                                         vpc_config=Vpc_configs_lambda,
                                         
                                         )

        # DynamoDB Stream event source mapping
        dynamdb_stream_lambda=LambdaEventSourceMapping(self, "lambd_function_stream_trigger",
                                                               function_name=lambda_function.function_name,
                                                               event_source_arn=dynamodb_table.stream_arn,
                                                               starting_position="LATEST"
                                                         )


app=App()
stack=MyStack(app, "learn-cdktf-dynamdb")
# RemoteBackend(stack,
#   hostname='app.terraform.io',
#   organization='example-org-8df812',
#   workspaces=NamedRemoteWorkspace('learn-cdktf-dynamdb')
# )

app.synth()
