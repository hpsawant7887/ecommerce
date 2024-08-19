from time import sleep
from flask import Flask, make_response
from src.dynamodb import DynamoDBClient


class EndpointHandler(object):
    def __init__(self, action, dynamodbclient=None):
        self.action = action
        self.dynamodbclient = dynamodbclient

    def __call__(self):
        response_body, status, headers = self.action(dynamodbclient=self.dynamodbclient)
        response = make_response(response_body, status)

        for header, value in headers.items():
            response.headers[header] = value

        return response
        # return make_response(response, status)


class FlaskServiceV2:
    def __init__(self, name):
        self.service = Flask(name)
        self.dynamodbclient = DynamoDBClient()

    def run(self, ip, port):
        self.service.run(host=ip, port=port)

    def add_endpoint(
            self,
            endpoint,
            endpoint_name,
            handler,
            methods=['GET']):
        self.service.add_url_rule(
            endpoint,
            endpoint_name,
            EndpointHandler(handler, self.mysqlclient, self.auth_mysqlclient),
            methods=methods)