import json
import hashlib
import uuid
import boto3
import os

from time import sleep
from flask import Flask, request, make_response
from src.mysqlclient import MySQLClient, database_exists, create_schema
from src.sqs import SqsClient

SQL_FILE = 'sql/onlinestore_schema.sql' 


class EndpointHandler(object):
    def __init__(self, action, mysqlclientObj=None, authmysqlclientObj=None):
        self.action = action
        self.mysqlclientObj = mysqlclientObj
        self.authmysqlclientObj = authmysqlclientObj

    def __call__(self):
        response_body, status, headers = self.action(mysqlclientObj=self.mysqlclientObj, authmysqlclientObj=self.authmysqlclientObj)
        response = make_response(response_body, status)

        for header, value in headers.items():
            response.headers[header] = value

        return response
        # return make_response(response, status)


class OnlineStoreService:
    def __init__(self, name, backend_db_info):
        self.service = Flask(name)
        self.db_endpoint = backend_db_info['endpoint']
        self.db_port = backend_db_info['port']
        self.db_user = backend_db_info['user']
        self.db_password = backend_db_info['password']
        self.db_name = backend_db_info['db_name']
        self.auth_db_name = backend_db_info['auth_db_name']

        self.check_and_create_db()

        self.mysqlclient = MySQLClient(self.db_endpoint,
                                       self.db_port,
                                       self.db_name,
                                       self.db_user,
                                       self.db_password
                                       )
        
        self.auth_mysqlclient = MySQLClient(self.db_endpoint,
                                       self.db_port,
                                       self.auth_db_name,
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
            EndpointHandler(handler, self.mysqlclient, self.auth_mysqlclient),
            methods=methods)
        

def health_check(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    try:
        return ('Health Check Success', 200, {})
    
    except Exception as e:
        return ('Internal Server Error', 500, {})
    

def verify_auth_header(func):
    def wrapper(**kwargs):
        try:
            if not request.authorization or not request.authorization.username or request.authorization.password:
                return (
                    'Access Denied!', 401, {
                        'WWW-Authenticate': 'Basic realm="Auth Required"'})

            get_password_query = "SELECT md5_password from users.credentials WHERE username={}".format(
                request.authorization.username)

            stored_password = kwargs["authmysqlclientObj"].executeQuery(get_password_query)[
                0]

            if stored_password != hashlib.md5(
                    request.authorization.password.encode('utf-8')).hexdigest():
                return ('Authentication Failed', 401, {})

            return func(**kwargs)
        except Exception as e:
            # return error
            return ('Internal Server Error', 500, {})

    return wrapper
    

#Customer facing endpoints
# @verify_auth_header
# def get_store_info(**kwargs):
#     if request.method != 'GET':
#         return ('Invalid method', 400, {})
    
#     try:
#         data = request.get_json(force=True)
#         if not data:
#             return ('Invalid Request Body', 400, {})
        
#         store_id = data['store_id']

#         query = "SELECT store_name, address from onlinestore.stores WHERE store_id={}".format(store_id)

#         res = kwargs["mysqlclientObj"].executeQuery(query)

#         return (json.dumps(res), 200, {'Content-Type': 'application/json'})

#     except Exception as e:
#         pass


@verify_auth_header
def get_product(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    data = request.get_json(force=True)
    if not data:
        return ('Invalid Request Body', 400, {})
        
    product_id = data['product_id']

    query = "SELECT product_id,product_name,product_description,price,available_quantity from onlinestore.products WHERE product_id={}".format(product_id)

    res = kwargs["mysqlclientObj"].executeQuery(query)

    return (json.dumps(res), 200, {'Content-Type': 'application/json'})

    
@verify_auth_header
def search_products(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    data = request.get_json(force=True)
    if not data:
        return ('Invalid Request Body', 400, {})
        
    search_key = data['search_key']

    query = "SELECT product_id,product_name,product_description,price,available_quantity FROM onlinestore.products WHERE product_name LIKE '%{}%' OR product_description LIKE '%{}%' ".format(search_key)

    res = kwargs["mysqlclientObj"].executeQuery(query)

    return (json.dumps(res), 200, {'Content-Type': 'application/json'})


# Create Store Owner (Seller)
def create_owner(**kwargs):
    try:
        if request.method != 'POST':
            return ('Invalid method', 400, {})
        
        data = request.get_json(force=True)

        if not data:
            return ('Invalid Request Body', 400, {})
        
        owner_id = uuid.uuid4().int
        
        query = "INSERT into onlinestore.owners (owner_id, first_name, last_name) VALUES ({}, {}, {})".format(owner_id, data['first_name'], data['last_name'])

        res = kwargs["mysqlclientObj"].executeQuery(query)

        return (json.dumps({'owner_id': owner_id}), 200, {'Content-Type': 'application/json'})
    except Exception as e:
        return ('Internal Server Error', 500, {})


# Get Store Owner Details


# Seller endpoints
def add_store(**kwargs):
    try:
        if request.method != 'POST':
            return ('Invalid method', 400, {})
        
        data = request.get_json(force=True)

        if not data:
            return ('Invalid Request Body', 400, {})
        
        store_name = data['store_name']
        store_address = data['store_address']
        owner_id = data['owner_id']
        store_id = uuid.uuid4().int
        
        query = "INSERT INTO onlinestore.stores (store_id,store_name, owner_id, address) VALUES ({}, {}, {}, {})".format(store_id,store_name,owner_id,store_address)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        kwargs["mysqlclientObj"].commit()

        return (json.dumps({'store_id': store_id}),200, {'Content-Type': 'application/json'})
    except Exception as e:
        return ('Internal Server Error', 500, {})


def delete_store(**kwargs):
    pass

def get_store_info(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    try:
        data = request.get_json(force=True)
        if not data:
            return ('Invalid Request Body', 400, {})
        
        store_id = data['store_id']

        query = "SELECT store_name, address from onlinestore.stores WHERE store_id={}".format(store_id)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        return (json.dumps(res), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        return ('Internal Server Error', 500, {})


def getStores(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    try:
        data = request.get_json(force=True)
        if not data:
            return ('Invalid Request Body', 400, {})
        
        owner_id = data['owner_id']

        query = "SELECT * from onlinestores.stores WHERE owner_id={}".format(owner_id)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        return (json.dumps(res), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        pass

def add_product(**kwargs):
    try:
        if request.method != 'POST':
            return ('Invalid method', 400, {})
        
        data = request.get_json(force=True)

        if not data:
            return ('Invalid Request Body', 400, {})
        
        product_name = data['product_name']
        product_description = data['product_description']
        owner_id = data['owner_id']
        store_id = data['store_id']
        product_id = uuid.uuid4().int
        price = float("{:.2f}".format(data['price']))
        available_quantity = data['available_quantity']

        query = "INSERT INTO onlinestore.products (product_id,product_name,store_id,owner_id,product_description,price,available_quantity) VALUES ({}, {}, {}, {}, {}, {}, {})".format(product_id, product_name, store_id, owner_id, product_description, price, available_quantity)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        kwargs["mysqlclientObj"].commit()

        return (json.dumps({'product_id': product_id, 'product_name': product_name}),200, {'Content-Type': 'application/json'})
    except Exception as e:
        return ('Internal Server Error', 500, {})

def delete_product(**kwargs):
    pass

def update_product(**kwargs):
    pass
    
# internal API
def increase_product_count(**kwargs):
    pass

def decrease_product_count(**kwargs):

    product_id = kwargs['product_id']
    ordered_quantity = kwargs['quantity']

    query = "UPDATE onlinestore.products SET available_quantity = available_quantity - {} WHERE product_id={}".format(ordered_quantity, product_id)

    res = kwargs["mysqlclientObj"].executeQuery(query)
    

def check_product_exists(**kwargs):
    pass
