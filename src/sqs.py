import os
import json
import boto3


class SqsClient:
    def __init__(self):
        role_arn = os.getenv('AWS_ROLE_ARN')

        with open(os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"), 'r') as content_file:
            web_identity_token = content_file.read()
        
        endpoint_url = os.getenv('SQS_VPC_ENDPOINT_URL')
        
        role = boto3.client('sts').assume_role_with_web_identity(RoleArn=role_arn, RoleSessionName='assume-role',
                                                             WebIdentityToken=web_identity_token)
        
        credentials = role['Credentials']
        aws_access_key_id = credentials['AccessKeyId']
        aws_secret_access_key = credentials['SecretAccessKey']
        aws_session_token = credentials['SessionToken']
        
        session = boto3.session.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                              aws_session_token=aws_session_token)
        
        self.sqs_client = session.client('sqs', endpoint_url=endpoint_url)


    def read_sqs_msg(self, sqs_queue_url):
        return self.sqs_client.receive_message(QueueUrl=sqs_queue_url, WaitTimeSeconds=5, MaxNumberOfMessages=10)
    

    def send_sqs_msg(self, sqs_queue_url, message):
        self.sqs_client.send_message(QueueUrl=sqs_queue_url, MessageBody=json.dumps(message))

    def delete_sqs_msg(self, sqs_queue_url, sqs_message_receipt):
        self.sqs_client.delete_message(QueueUrl=sqs_queue_url, ReceiptHandle=sqs_message_receipt)


