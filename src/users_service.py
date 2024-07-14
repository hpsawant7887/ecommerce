import json
import hashlib
import uuid

from flask import Flask, request, make_response
from src.mysqlclient import MySQLClient, database_exists

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


class UserService:
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

        with open(SQL_FILE) as fd:
            stmts = fd.read().split(';')
            for query in stmts:
                q = query.replace('\n', '')
                results = self.mysqlclient.executeQuery(q)

        self.mysqlclient.commit()

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



def register_user_action(mysqlclientObj):
    if request.method != 'POST':
        # return error
        return ('Invalid method', 400, {})

    try:
        data = request.get_json(force=True)

        if not data:
            return ('Invalid Request Body', 400, {})

        username = data['username']
        password = hashlib.md5(data['password'].encode('utf-8')).hexdigest()
        first_name = data['first_name']
        last_name = data['last_name']
        email = data['username']
        address = data['address']
        user_id = uuid.uuid4().int

        user_info_query = """INSERT into users.user_info (user_id, username, first_name, \
            last_name, email, user_address) values ({}, {}, {}, {}, {}, {})""".format(
            user_id, username, first_name, last_name, email, address)

        mysqlclientObj.executeQuery(user_info_query)

        user_creds_query = """ INSERT into users.credentials (user_id, username, \
            md5_password) values ({} {} {})""".format(user_id, username, password)

        mysqlclientObj.executeQuery(user_creds_query)

        mysqlclientObj.commit()

        return ('User Registration Complete', 200, {})

    except Exception as e:
        # return error
        return ('Internal Server Error', 500, {})


def health_check():
    if request.method != 'HEAD':
        return ('Invalid method', 400, {})
    
    try:
        return ('Health Check Success', 200, {})
    
    except Exception as e:
        return ('Internal Server Error', 500, {})




# Implement *args for func
def verify_auth_header(func):
    def wrapper(mysqlclientObj):
        try:
            if not request.authorization or not request.authorization.username or request.authorization.password:
                return (
                    'Access Denied!', 401, {
                        'WWW-Authenticate': 'Basic realm="Auth Required"'})

            get_password_query = "SELECT md5_password from users.credentials WHERE username={}".format(
                request.authorization.username)

            stored_password = mysqlclientObj.executeQuery(get_password_query)[
                0]

            if stored_password != hashlib.md5(
                    request.authorization.password.encode('utf-8')).hexdigest():
                return ('Authentication Failed', 401, {})

            return func(mysqlclientObj)
        except Exception as e:
            # return error
            return ('Internal Server Error', 500, {})

    return wrapper


@verify_auth_header
def get_user_info(mysqlclientObj):
    user_info_query = "SELECT username, first_name, last_name, email, address from users.user_info WHERE username={}".format(
        request.authorization.username)

    res = mysqlclientObj.executeQuery(user_info_query)

    return (json.dumps(res), 200, {'Content-Type': 'application/json'})
