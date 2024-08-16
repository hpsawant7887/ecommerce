from time import sleep
from flask import Flask, make_response
from src.mysqlclient import MySQLClient, database_exists, create_schema


class EndpointHandler(object):
    def __init__(self, action, mysqlclientObj=None):
        self.action = action
        self.mysqlclientObj = mysqlclientObj
        #self.authmysqlclientObj = authmysqlclientObj

    def __call__(self):
        response_body, status, headers = self.action(mysqlclientObj=self.mysqlclientObj)
        response = make_response(response_body, status)

        for header, value in headers.items():
            response.headers[header] = value

        return response
        # return make_response(response, status)


class FlaskService:
    def __init__(self, name, sql_file, backend_db_info):
        self.service = Flask(name)
        self.db_endpoint = backend_db_info.get('endpoint', None)
        self.db_port = backend_db_info.get('port', None)
        self.db_user = backend_db_info.get('user', None)
        self.db_password = backend_db_info.get('password', None)
        self.db_name = backend_db_info.get('db_name', None)
        #self.auth_db_name = backend_db_info.get('auth_db_name', None)
        self.sql_file_path = sql_file

        if self.db_name:
            self.check_and_create_db()

        if self.db_name:
            self.mysqlclient = MySQLClient(self.db_endpoint,
                                       self.db_port,
                                       self.db_name,
                                       self.db_user,
                                       self.db_password
                                       )
        else:
            self.mysqlclient = None
        
        # if self.auth_db_name:
        #     self.auth_mysqlclient = MySQLClient(self.db_endpoint,
        #                                     self.db_port,
        #                                     self.auth_db_name,
        #                                     self.db_user,
        #                                     self.db_password
        #                                     )
        # else:
        #     self.auth_mysqlclient = None

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
            EndpointHandler(handler, self.mysqlclient),
            methods=methods)
