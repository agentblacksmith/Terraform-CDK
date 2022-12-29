# Terraform CDK project with Opensearch, DynamoDB
## Table of Content
* [Project Assumption](#project-assumptions)
* [About DynamoDB](#dyanmodb)

This project motive is to create a stack with AWS opensearch, Dynamodb. 
The Stack includes, 
1. DynamoDB Table
2. Lambda Function
3. Opensearch Domain
---
## Project Assumptions
1. The roles and policies were created prior to the project. The ARN's for the resources were assumeed with the resource name combined in the [AWS ARN format](https://docs.aws.amazon.com/general/latest/gr/aws-arns-and-namespaces.html)
2. The VPC, subnet and security groups were created before the project and utilized here. These can also be automated and in the future versions of this project we can see that. Also only one subnet was created, this was accidently done. Will be creating more.
3. The opensearch is only single zone to reduce the additional costs.
4. Most of the variables are defined in the same file which can also be changed to a configuration file and loaded at run time.

---
## DyanmoDB
In here I made use of one Dynamdb table with with a Partition key and a sorting key. There were no global secondary index created but it is a good practice to have them on the production usages.








The current project is used a single stack and it is not a best practice to write everything in a single Class init method. This area need improvement and need to check what are the possibilities to make the methods more general.

This stack didn't utilize the terraform modules yet, these are something that I have read about and I strongly believe we have to use it. From what I have read so far these modules can be included as part of the `cdktf.json` file. Need more insight in these.

