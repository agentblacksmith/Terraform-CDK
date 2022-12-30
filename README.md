# Terraform CDK with Opensearch & DynamoDB

![Terraform](https://img.shields.io/badge/terraform-%235835CC.svg?style=for-the-badge&logo=terraform&logoColor=white) <img src="http://ForTheBadge.com/images/badges/made-with-python.svg" alt="drawing" style="width:1900px;"/> 



## Table of Content
* [Project Assumptions](#project-assumptions)
* [About CDK](#initializing-cdk-↑)
* [About DynamoDB](#dyanmodb-↑)
* [About Lambda](#lambda-function-↑)
* [About Opensearch](#opensearch-domain-↑)
* [About IAM Resources](#iam-resources-↑)
* [Scope for Improvements](#scope-of-improvements-↑)
* [Further Reading](#further-reading-↑)

This project motive is to create a stack with AWS opensearch, Dynamodb. For reference I have used the contents from the [AWS Official Documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/integrations.html#integrations-dynamodb)

The Stack includes, 
1. DynamoDB Table
2. Lambda Function
3. Opensearch Domain
4. Supported IAM Roles and Policy
5. A sample cloud watch metric alarm for opensearch (more will be added as part of the improvement)
---
## Project Assumptions
1. The VPC, subnet and security groups were created before the project and utilized here. These can also be automated and in the future versions of this project we can see that. Also only one subnet was created, this was accidently done. Will be creating more.
2. The opensearch is only single zone to reduce the additional costs.
3. Most of the variables are defined in the same file which can also be changed to a configuration file and loaded at run time.
4. Project used `python` as the template.

---
## Initializing CDK [↑](#table-of-content)
**[Documentation](https://developer.hashicorp.com/terraform/cdktf)**
> Installation guide: [CDKTF](https://developer.hashicorp.com/terraform/tutorials/cdktf/cdktf-install)

After `cdktf` installed, initialize inside and empty directory using the cdk:
```shell
cdktf init --template=python
```
This initializes the terraform with backend as terraform cloud. 
We can add our code in the `main.py` in the `__init__` function created for our stack by cdktf.
> **Note:** I had a few issues with setting this up but I wanted to try this option so used the same. Still have some issue so the current project is using the local `tfstate` file. 
> 
> The S3 backend will be implemented soon with dynamodb table lock.
---
## DyanmoDB [↑](#table-of-content)
**[Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Introduction.html)**

Here I made use of a Dynamdb table with with Partition key and sorting key. There were no global secondary index created but it is a good practice to have them on the production usages.
The following variables were used:
```python
# DynamoDB varialbes
DynamoDB_Table          = "GameScores"
DynamoDB_Billing        = "PAY_PER_REQUEST"
DynamoDB_Partion_Key    = 'UserId'
DynamoDB_Sortkey        = 'GameTitle'
DynamoDB_Attribute_Type = 'S'
```
The main parameters used in dynamodb creation for the security and maintainability are:
1. `billing_mode`: I used the `PAY_PER_REQUEST` for the demo but for production usecases we have to make use of `PROVISIONED` mode (Default). [About billing_mode](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/dynamodb_table#billing_mode)
2. `hash_key`: This is the partition key and it is a mandatory field as far as the dynamodb is considered. 
3. `server_side_encryption`: This values is used to encrypt the data at rest and AWS KMS key is being used for this purpose.
4. `stream_enabled`: This value is set to `True` for the streams to be sent for processing. This helps in better maintainablility. The trigger is a [Lambda function](#lambda-function) created as part of the stack.

* An `IAM Role` was created for the accessibility with only the base access permissions. The policy documenation can be found [here](policy.json). More can be found in the [IAM Resources](#iam-resources-↑) section. I had made use of some of the best practices like *Encryption at rest*, *Use IAM roles to authenticate access to DynamoDB* etc as mentioned [here](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices-security-preventative.html). 
* Apart from this we can also enable the **Point-in-time recovery (PITR)** for *the continuous backups of your DynamoDB data for 35 days to help you protect against accidental write or deletes* and as well as the **Global Replicas** for high availability. These values were not set because it may incur some additional charges.

The dynamodb is also enabled with the **DynamoDB Streams** with `New and old images` as the `view type`. With this we can not only capture the new changes, but can also view what was the state before change. These are logged in the Cloudwatch logs using the `Lambda Function` trigger. More about this Lambda function refer [here](#lambda-function-↑)


---
## Lambda Function [↑](#table-of-content)
**[Documentation]()**

---
## Opensearch Domain [↑](#table-of-content)
**[Documentation]()**

---
## IAM Resources [↑](#table-of-content)
**[Documentation]()**

---
## Scope of Improvements [↑](#table-of-content)
* The current project used a single stack and it is not a best practice to write everything in a single Class init method. This area need improvement and need to check what are the possibilities to make the methods more general.

* This stack didn't utilize the terraform modules yet, these are something that I have read about and I strongly believe we have to use it. From what I have read so far these modules can be included as part of the `cdktf.json` file. Need more insight in these.

* Cloudwatch monitoring for all the services with important alerts.

---
## Further Reading [↑](#table-of-content)
* CDKTF
    - [link1]()
    - [link2]()
* Dynamodb
    - [link1]()
    - [link2]()
* Lambda
    - [link1]()
    - [link2]()
* Opensearch Domain
    - [link1]()
    - [link2]()
* IAM Resouces
    - [link1]()
    - [link2]()