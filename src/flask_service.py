from time import sleep
from flask import Flask, request, make_response
from src.mysqlclient import MySQLClient, database_exists, create_schema


class EndpointHandler(object):
    def __init__(self, action, mysqlclientObj=None, authmysqlclientObj=None):
        self.action = action
        self.mysqlclientObj = mysqlclientObj
        self.authmysqlclientObj = authmysqlclientObj

    def __call__(self):
        response_body, status, headers = self.action(
            mysqlclientObj=self.mysqlclientObj, authmysqlclientObj=self.authmysqlclientObj)
        response = make_response(response_body, status)

        for header, value in headers.items():
            response.headers[header] = value

        return response
        # return make_response(response, status)


class FlaskService:
    def __init__(self, name, sql_file, backend_db_info):
        self.service = Flask(name)
        self.db_endpoint = backend_db_info['endpoint']
        self.db_port = backend_db_info['port']
        self.db_user = backend_db_info['user']
        self.db_password = backend_db_info['password']
        self.db_name = backend_db_info['db_name']

        self.auth_db_name = backend_db_info.get('auth_db_name', None)
        self.sql_file_path = sql_file

        self.check_and_create_db()

        self.mysqlclient = MySQLClient(self.db_endpoint,
                                       self.db_port,
                                       self.db_name,
                                       self.db_user,
                                       self.db_password
                                       )
        
        if self.auth_db_name:
            self.auth_mysqlclient = MySQLClient(self.db_endpoint,
                                            self.db_port,
                                            self.auth_db_name,
                                            self.db_user,
                                            self.db_password
                                            )
        else:
            self.auth_mysqlclient = None

    def check_and_create_db(self):
        if database_exists(
                self.db_endpoint,
                self.db_port,
                self.db_name,
                self.db_user,
                self.db_password):
            return

        create_schema(
            self.db_endpoint,
            self.db_port,
            self.db_user,
            self.db_password,
            self.sql_file_path)

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
            EndpointHandler(handler, self.mysqlclient, self.auth_mysqlclient),
            methods=methods)
