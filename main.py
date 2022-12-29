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
from cdktf_cdktf_provider_aws.iam_policy import IamPolicy
from cdktf_cdktf_provider_aws.iam_role_policy_attachment import IamRolePolicyAttachment


# AWS variables
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
Account_ID = os.environ.get("ACCOUNT_ID", "865227664036")

# IAM variables
# Service_role = os.environ.get("SERVICE_ROLE","dynamodb-opeansearch-stream-lambda-role-ocu941je")
# Service_role_arn = f"arn:aws:iam::{Account_ID}:role/service-role/{Service_role}"
with open(os.path.abspath('policy.json')) as policy_doc:
    Policy_doc = json.load(policy_doc)
with open(os.path.abspath('lambda_assume_policy.json')) as policy_doc:
    Assume_policy = json.load(policy_doc)
with open(os.path.abspath('opensearch_polciy.json')) as policy_doc:
    Opensearch_policy = json.load(policy_doc)

IAM_resource_ID = "lambda-opensearch-dynamdb"
IAM_policy_name = f"{IAM_resource_ID}-iam"
IAM_role_name = f"{IAM_resource_ID}-role"

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
Lambda_Function_Timeout = 30
Lambda_log_retention = 3

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
# Opensearch_domain_arn = f"arn:aws:es:us-east-1:{Account_ID}:domain/"


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)
        AwsProvider(self, "AWS", region=AWS_REGION)

        # IAM Policy
        iam_policy = IamPolicy(self,
                               IAM_policy_name,
                               name=IAM_policy_name,
                               description='lambda to handle dynamodb stream and opensearch',
                               policy=json.dumps(Policy_doc)
                               )
        iam_role = IamRole(self,
                           IAM_role_name,
                           name=IAM_role_name,
                           description='Role to give permission for lambda to access different resources',
                           assume_role_policy=json.dumps(Assume_policy)
                           )
        IamRolePolicyAttachment(self, "Role-policy-attachment",
                                role=iam_role.name,
                                policy_arn=iam_policy.arn
                                )

        # Cloudwatch log group creation
        CloudwatchLogGroup(self, "LogGroup", name=Lambda_Function_Log_Group,
                           retention_in_days=Lambda_log_retention)

        # DynamoDB Table
        dynamodb_table = DynamodbTable(self, "dynamodb",
                                       name=DynamoDB_Table,
                                       billing_mode=DynamoDB_Billing,
                                       hash_key=DynamoDB_Partion_Key,
                                       range_key=DynamoDB_Sortkey,
                                       server_side_encryption={
                                           "enabled": True
                                       },
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
        opensearch_domain = OpensearchDomain(self, Opensearch_domain,
                                             domain_name=Opensearch_domain,
                                             engine_version=Opensearch_version,
                                             vpc_options=Vpc_configs_opensearch,
                                             cluster_config={
                                                 "dedicated_master_count": Opnesearch_dedicated_master_count,
                                                 "dedicated_master_enabled": Opensearch_dedicated_master_enabled,
                                                 "instance_count": Opensearch_data_node_count,
                                                 "instance_type": Opensearch_instance_type,
                                                 "zone_awareness_enabled": Opensearch_zone_awareness_enabled
                                             },
                                             #  access_policies         = json.dumps(Opensearch_policy),
                                             domain_endpoint_options=OpensearchDomainDomainEndpointOptions(
                                                 enforce_https=True,
                                                 tls_security_policy=Opensearch_ttl_policy),
                                             ebs_options=OpensearchDomainEbsOptions(
                                                 ebs_enabled=Opensearch_ebs_enabled, volume_size=Opensearch_volume_size),
                                             encrypt_at_rest={
                                                 "enabled": True
                                             }
                                             )
        Opensearch_policy["Statement"][0]["Resource"] = opensearch_domain.arn
        opensearch_domain.access_policies = json.dumps(Opensearch_policy)

        # Lambda function creation
        lambda_function = LambdaFunction(self, Lambda_Function_Name,
                                         function_name=Lambda_Function_Name,
                                         runtime="python3.8",
                                         handler=Lambda_Function_Handler,
                                         filename=os.path.abspath(
                                             Lambda_Function_Payload),
                                         role=iam_role.arn,
                                         environment=LambdaFunctionEnvironment(
                                             variables={
                                                 "ENDPOINT": f"https://{opensearch_domain.endpoint}"
                                             }
                                         ),
                                         publish=True,
                                         timeout=Lambda_Function_Timeout,
                                         depends_on=[opensearch_domain],
                                         vpc_config=Vpc_configs_lambda,
                                         )

        # DynamoDB Stream event source mapping
        dynamdb_stream_lambda = LambdaEventSourceMapping(self, "lambd_function_stream_trigger",
                                                         function_name=lambda_function.function_name,
                                                         event_source_arn=dynamodb_table.stream_arn,
                                                         starting_position="LATEST"
                                                         )
        # Add dynamdb arn and opensearch arn to policy
        Policy_doc['Statement'][1]['Resource'].append(opensearch_domain.arn)
        Policy_doc['Statement'][1]['Resource'].append(
            dynamdb_stream_lambda.arn)
        iam_policy.policy = json.dumps(Policy_doc)


app = App()
stack = MyStack(app, "learn-cdktf-dynamdb")
RemoteBackend(stack,
              hostname='app.terraform.io',
              organization='example-org-8df812',
              workspaces=NamedRemoteWorkspace('learn-cdktf-dynamdb')
              )

app.synth()
