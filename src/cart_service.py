import json
import hashlib
import uuid

from flask import Flask, request, make_response
from src.mysqlclient import MySQLClient, database_exists, create_schema

SQL_FILE = 'sql/user_schema.sql'

class EndpointHandler(object):
    def __init__(self, action, mysqlclientObj=None):
        self.action = action
        self.mysqlclientObj = mysqlclientObj

    def __call__(self):
        response_body, status, headers = self.action(self.mysqlclientObj)
        response = make_response(response_body, status)

        for header, value in headers.items():
            response.headers[header] = value

        return response
        # return make_response(response, status)


class CartService:
    def __init__(self, name, backend_db_info):
        self.service = Flask(name)
        self.db_endpoint = backend_db_info['endpoint']
        self.db_port = backend_db_info['port']
        self.db_user = backend_db_info['user']
        self.db_password = backend_db_info['password']
        self.db_name = backend_db_info['db_name']

        self.check_and_create_db()

        self.mysqlclient = MySQLClient(self.db_endpoint,
                                       self.db_port,
                                       self.db_name,
                                       self.db_user,
                                       self.db_password
                                       )

    def check_and_create_db(self):
        if database_exists(
                self.db_endpoint,
                self.db_port,
                self.db_name,
                self.db_user,
                self.db_password):
            return

        create_schema(self.db_endpoint, self.db_port, self.db_user, self.db_password, SQL_FILE)

        # self.mysqlclient.commit()

    def run(self, ip, port):
        self.check_and_create_db()

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
            EndpointHandler(handler, self.mysqlclient),
            methods=methods)