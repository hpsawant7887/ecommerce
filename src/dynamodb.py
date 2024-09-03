import os
import json
import boto3
import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class DynamoDBClient:
    def __init__(self):
        self.role_arn = os.getenv('AWS_ROLE_ARN')
        with open(os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"), 'r') as content_file:
            web_identity_token = content_file.read()

        self.web_identity_token = web_identity_token

    
    def set_creds(self):
        role = boto3.client('sts').assume_role_with_web_identity(RoleArn=self.role_arn, RoleSessionName='assume-role',
                                                             WebIdentityToken=self.web_identity_token)
        
        credentials = role['Credentials']
        aws_access_key_id = credentials['AccessKeyId']
        aws_secret_access_key = credentials['SecretAccessKey']
        aws_session_token = credentials['SessionToken']


        session = boto3.session.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
                              aws_session_token=aws_session_token)
        

        self.dynamodb_client = session.client('dynamodb')
        self.dynamodb_res = session.resource('dynamodb')


    def create_dynamodb_item(self, dynamo_table, ddb_item):
        try:
            ddb_table = self.dynamodb_res.Table(dynamo_table)
            res = ddb_table.put_item(Item=ddb_item,)


            # return self.dynamodb_client.update_item(TableName=dynamo_table,
            #                                  Key={primary_key: {"S": key_value}},
            #                                  AttributeUpdates=attribute_data)

            return res['ResponseMetadata']['HTTPStatusCode']

        except ClientError as error:
            raise RuntimeError("Failed to enter item into Dynamo Table {} {}".format(dynamo_table, error))


    def update_dynamodb_item(self, dynamo_table, Key, UpdateExpression, ExpressionAttributeValues=None, ExpressionAttributeNames=None, ConditionExpression=None):
        try:
            ddb_table = self.dynamodb_res.Table(dynamo_table)
            if ExpressionAttributeNames and ConditionExpression:
                response = ddb_table.update_item(Key=Key, UpdateExpression=UpdateExpression,
                                                ExpressionAttributeValues=ExpressionAttributeValues,
                                                ExpressionAttributeNames=ExpressionAttributeNames,
                                                ConditionExpression=ConditionExpression,
                                                ReturnValues="UPDATED_NEW")
                
            elif ExpressionAttributeNames and ExpressionAttributeValues:
                response = ddb_table.update_item(Key=Key, UpdateExpression=UpdateExpression,
                                               ExpressionAttributeValues=ExpressionAttributeValues,
                                               ExpressionAttributeNames=ExpressionAttributeNames,
                                               ReturnValues="UPDATED_NEW")
               
            elif ExpressionAttributeNames and not ExpressionAttributeValues:
                 response = ddb_table.update_item(Key=Key, UpdateExpression=UpdateExpression,
                                               ExpressionAttributeNames=ExpressionAttributeNames,
                                               ReturnValues="UPDATED_NEW")
                 
            elif ExpressionAttributeValues and not ExpressionAttributeNames:
                response = ddb_table.update_item(Key=Key, UpdateExpression=UpdateExpression,
                                               ExpressionAttributeValues=ExpressionAttributeValues,
                                               ReturnValues="UPDATED_NEW")

            else:
              response = ddb_table.update_item(Key=Key, UpdateExpression=UpdateExpression,
                                               ReturnValues="UPDATED_NEW")

            return response['ResponseMetadata']['HTTPStatusCode']
        except ClientError as error:
               logger = logging.getLogger(__name__)
               raise RuntimeError("Failed to update Dynamo Table {}".format(dynamo_table))


    def delete_dynamodb_item(self, dynamo_table, Key):
        try:
            ddb_table = self.dynamodb_res.Table(dynamo_table)
            response = ddb_table.delete_item(Key=Key)
            return response['ResponseMetadata']['HTTPStatusCode']
            # return self.dynamodb_client.delete_item(TableName=dynamo_table,
            #                                  Key={primary_key: {"S": key_value}})
        except ClientError as error:
                raise RuntimeError("Failed to delete Dynamo Key {} {}".format(Key, error))

    
    def get_dynamodb_item(self, dynamo_table, Key):
        try:
            ddb_table = self.dynamodb_res.Table(dynamo_table)
            response = ddb_table.get_item(Key=Key)

            return response['Item']
            
            # return self.dynamodb_client.get_item(TableName=dynamo_table,
            #                               Key={primary_key: {"S": key_value}})
        except ClientError as error:
            raise RuntimeError("Failed to get Dynamo Item {} {}".format(Key, error))