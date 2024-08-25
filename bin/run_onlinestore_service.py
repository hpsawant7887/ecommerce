import os
import threading
import json
import hashlib
import logging

import uuid
import requests

from flask import request
from src.flask_service import FlaskService
from src.sqs import SqsClient
from time import sleep
from src.k8s_utils import get_service_endpoint

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

SQL_FILE = 'sql/onlinestore_schema.sql'


def start_sqs_listener(sqs_queue_url, onlinestore_service_obj):
    sqs_client_obj = SqsClient()

    while True:
        sqs_messages = sqs_client_obj.read_sqs_msg(sqs_queue_url)

        if 'Messages' not in sqs_messages:
            sleep(300)
            continue

        for sqs_message in sqs_messages['Messages']:
            msg = json.loads(sqs_message['Body'])
            sqs_client_obj.delete_sqs_msg(sqs_queue_url, sqs_message['ReceiptHandle'])

            if msg['type'] == "NewOrderReceived":
                order = {
                    "order_id": msg['order_id'],
                    "products": msg['products']
                }

                for product in order["products"]:
                    product_id = product['product_id']
                    quantity = product['quantity']
                    decrease_product_count(mysqlclientObj=onlinestore_service_obj.mysqlclient, product_id=product_id, quantity=quantity)
            else:
                #illegal messageType
                pass


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
            if not request.authorization or not request.authorization.username or not request.authorization.password:
                return (
                    'Access Denied!', 401, {
                        'WWW-Authenticate': 'Basic realm="Auth Required"'})

            # get_password_query = "SELECT md5_password from users.credentials WHERE username={}".format(
            #     request.authorization.username)

            # stored_password = kwargs["authmysqlclientObj"].executeQuery(get_password_query)[
            #     0]

            # if stored_password != hashlib.md5(
            #         request.authorization.password.encode('utf-8')).hexdigest():
            #     return ('Authentication Failed', 401, {})
            
            users_service_endpoint = get_service_endpoint('users-service', 'users-service')

            auth_url = 'http://{}/users-service-internal/verify_user'.format(users_service_endpoint)

            data = {
                'username': request.authorization.username,
                'password': request.authorization.password
            }

            resp = requests.post(auth_url, data=json.dumps(data))

            if resp.code != 200:
                return ('Authentication Failed', 401, {})

            return func(**kwargs)
        except Exception as e:
            logger.error(e)
            return ('Internal Server Error', 500, {})

    return wrapper


@verify_auth_header
def get_product(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    product_id = request.args.get('productId')

    query = "SELECT product_id,product_name,product_description,price,available_quantity from onlinestore.products WHERE product_id='{}'".format(product_id)

    res = kwargs["mysqlclientObj"].executeQuery(query)[0]

    product_info = {
        'product_id': res[0],
        'product_name': res[1],
        'product_description': res[2],
        'price': res[3],
        'available_quantity': res[4]
    }

    return (json.dumps(product_info), 200, {'Content-Type': 'application/json'})

    
@verify_auth_header
def search_products(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    search_key = request.args.get('searchKey')

    query = "SELECT product_id,product_name,product_description,price,available_quantity FROM onlinestore.products WHERE product_name LIKE '%{}%' OR product_description LIKE '%{}%' ".format(search_key)

    res = kwargs["mysqlclientObj"].executeQuery(query)

    products = {'products': []}

    for product in res:
        p = {}
        p['product_id'] = product[0]
        p['product_name'] = product[1]
        p['product_description'] = product[2]
        p['price'] = product[3]
        p['available_quantity'] = product[4]

        products['products'].append(p)

    return (json.dumps(products), 200, {'Content-Type': 'application/json'})


def add_product(**kwargs):
    try:
        if request.method != 'POST':
            return ('Invalid method', 400, {})
        
        data = request.get_json(force=True)

        if not data:
            return ('Invalid Request Body', 400, {})
        
        product_name = data['product_name']
        product_description = data['product_description']
        product_id = uuid.uuid1().int >> 64
        price = float("{:.2f}".format(data['price']))
        available_quantity = data['available_quantity']

        query = "INSERT INTO onlinestore.products (product_id,product_name,product_description,price,available_quantity) VALUES ({},'{}','{}',{},{})".format(product_id, product_name, product_description, price, available_quantity)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        kwargs["mysqlclientObj"].commit()

        return (json.dumps({'product_id': product_id, 'product_name': product_name}),200, {'Content-Type': 'application/json'})
    except Exception as e:
        logger.error(e)
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

    kwargs["mysqlclientObj"].commit()
    

def check_product_exists(**kwargs):
    pass


def main():
    backend_db_info = {
        "endpoint": os.environ['RDS_MYSQL_ENDPOINT'],
        "port": os.environ['RDS_MYSQL_PORT'],
        "user": os.environ['RDS_MYSQL_USER'],
        "password": os.environ['RDS_MYSQL_PASSWORD'],
        "db_name": os.environ['RDS_MYSQL_DB_NAME']
    }

    sqs_queue_url = os.environ['SQS_QUEUE_URL_ORDERING_TO_ONLINE_STORE']

    onlinestore_service_obj = FlaskService('demo-eshop-online-store-service', SQL_FILE, backend_db_info)

    onlinestore_service_obj.mysqlclient.setConnection()

    t1 = threading.Thread(target=start_sqs_listener, args=(sqs_queue_url, onlinestore_service_obj,))
    t1.start()

    onlinestore_service_obj.add_endpoint(
        endpoint='/onlinestore-service/healthCheck',
        endpoint_name='healthCheck',
        handler=health_check)

    onlinestore_service_obj.add_endpoint(
        endpoint='/onlinestore-service/searchProducts',
        endpoint_name='searchProducts',
        handler=search_products)

    onlinestore_service_obj.add_endpoint(
        endpoint='/onlinestore-service/getProductInfo',
        endpoint_name='getProductInfo',
        handler=get_product)
    
    onlinestore_service_obj.add_endpoint(
        endpoint='/onlinestore-service/addProduct',
        endpoint_name='addProduct',
        handler=add_product,
        methods=['POST'])
    
    onlinestore_service_obj.run("0.0.0.0", 8081)

    t1.join()
    

if __name__ == '__main__':
    main()