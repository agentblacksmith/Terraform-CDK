import boto3
import requests
from requests_aws4auth import AWS4Auth
import os

region = os.environ.get('REGION','us-east-1') # e.g. us-east-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

host =  os.environ.get('ENDPOINT') # the OpenSearch Service domain, e.g. https://search-mydomain.us-west-1.es.amazonaws.com
index2 = 'orders'
datatype = '_doc'
url2 = host + '/' + index2 + '/' + datatype + '/'

headers = { "Content-Type": "application/json" }

def handler(event, context):
    count = 0

    for record in event['Records']:
        # Get the primary key for use as the OpenSearch ID
        id = record['dynamodb']['Keys']['UserId']['S']

        if record['eventName'] == 'REMOVE':
            r = requests.delete(url2 + id, auth=awsauth)
        else:
            document = record['dynamodb']['NewImage']
            r = requests.put(url2 + id, auth=awsauth, json=document, headers=headers)
        count += 1
        r = requests.get(f"{host}/{index2}",auth = awsauth)
        print(r.text)
        r = requests.get(f"{host}/{index2}",auth = awsauth)
        print(r.text)
    return str(count) + ' records processed.'
