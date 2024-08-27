import os
import threading
import json
import hashlib
import logging
import uuid
import requests

from flask import request
from src.flask_service_v2 import FlaskServiceV2
from src.k8s_utils import get_service_endpoint
from src.sqs import SqsClient
from src.dynamodb import DynamoDBClient
from time import sleep

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def get_unique_cart_id():
    return uuid.uuid4().hex

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
            
            users_service_endpoint = get_service_endpoint('demo-eshop-users-service', 'users-service')

            auth_url = 'http://{}/users-service-internal/verify_user'.format(users_service_endpoint)

            data = {
                'username': request.authorization.username,
                'password': request.authorization.password
            }

            resp = requests.post(auth_url, data=json.dumps(data))

            if resp.status_code != 200:
                return ('Authentication Failed', 401, {})

            return func(**kwargs)
        except Exception as e:
            # return error
            return ('Internal Server Error', 500, {})

    return wrapper

@verify_auth_header
def create_cart(**kwargs):
    if request.method != 'POST':
        return ('Invalid method', 400, {})
    try:
        data = request.get_json(force=True)
        user_id = int(data['userId'])
        dynamodbclient = kwargs['dynamodbclient']

        cart_id = get_unique_cart_id()

        ddb_item = {
            'cart_id': cart_id,
            'user_id': user_id,
            'products': {}
        }

        res = dynamodbclient.create_dynamodb_item('carts', ddb_item)

        return (json.dumps(res), 200, {})
    
    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})

@verify_auth_header
def get_cart(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    try:
        cart_id = request.args.get('cartId')
        user_id = request.args.get('userId')

        dynamodbclient = kwargs['dynamodbclient']

        primary_key = 'cart_id'
        key_value = cart_id
        secondary_key = 'user_id'
        secondary_key_value = user_id

        Key= {
            primary_key: key_value,
            secondary_key: secondary_key_value
        }

        res = dynamodbclient.get_dynamodb_item('carts', Key)

        return (json.dumps(res), 200, {})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@verify_auth_header
def addToCart(**kwargs):
    if request.method != 'PUT':
        return ('Invalid method', 400, {})
    try:
        data = request.get_json(force=True)
        user_id = data['userId']
        cart_id = data['cartId']
        product_id = data['productId']
        quantity = data['quantity']

        dynamodbclient = kwargs['dynamodbclient']

        primary_key = 'cart_id'
        key_value = cart_id
        secondary_key = 'user_id'
        secondary_key_value = user_id

        Key= {
            primary_key: key_value,
            secondary_key: secondary_key_value
        }

        UpdateExpression = 'SET products.#product_id = :quantity'
        ExpressionAttributeNames = {
            "#product_id": product_id
        }
        ExpressionAttributeValues = {
            ":quantity": quantity
        }

        res = dynamodbclient.update_dynamodb_item('carts', Key, UpdateExpression, ExpressionAttributeValues, ExpressionAttributeNames)

        return ('Added to Cart', 200, {})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@verify_auth_header
def removeFromCart(**kwargs):
    try:
        data = request.get_json(force=True)
        cart_id = data['cartId']
        user_id = data['userId']
        product_id = data['productId']

        dynamodbclient = kwargs['dynamodbclient']

        primary_key = 'cart_id'
        key_value = cart_id
        secondary_key = 'user_id'
        secondary_key_value = user_id

        Key= {
            primary_key: key_value,
            secondary_key: secondary_key_value
        }

        UpdateExpression = "REMOVE products.#product_id"
        ExpressionAttributeNames = {
            "#product_id": product_id
        }
        ExpressionAttributeValues = None

        res = dynamodbclient.update_dynamodb_item('carts', Key, UpdateExpression, ExpressionAttributeValues, ExpressionAttributeNames)

        return ('', 200, {})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@verify_auth_header
def deleteCart(**kwargs):
    try:
        data = request.get_json(force=True)
        cart_id = data['cartId']
        user_id = data['userId']

        dynamodbclient = kwargs['dynamodbclient']

        primary_key = 'cart_id'
        key_value = cart_id

        secondary_key = 'user_id'
        secondary_key_value = user_id

        Key= {
            primary_key: key_value,
            secondary_key: secondary_key_value
        }

        res = dynamodbclient.delete_dynamodb_item('carts', Key)

        return ('Cart {} for user_id {} deleted'.format(cart_id, user_id), 200, {})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@verify_auth_header
def update_ddb(**kwargs):
    pass


def start_sqs_listener(sqs_queue_url, cart_service_obj):
    sqs_client_obj = SqsClient()

    while True:
        sqs_messages = sqs_client_obj.read_sqs_msg(sqs_queue_url)

        if 'Messages' not in sqs_messages:
            sleep(300)
            continue

        for sqs_message in sqs_messages['Messages']:
            msg = json.loads(sqs_message['Body'])
            sqs_client_obj.delete_sqs_msg(sqs_queue_url, sqs_message['ReceiptHandle'])

            if msg['type'] == "OrderPlaced":
                order = {
                    "order_id": msg['order_id'],
                    "cart_id": msg['cart_id']
                }

                cart_id = msg['cart_id']

                primary_key = 'cart_id'
                key_value = cart_id

                Key= {primary_key: key_value}

                dynamodbclient = cart_service_obj.dynamodbclient

                res = dynamodbclient.delete_dynamo_item('carts', Key)

            else:
                #illegal messageType
                pass

def main():
    sqs_queue_url = os.environ['SQS_QUEUE_URL_ORDERING_TO_CARTS']

    cart_service_obj = FlaskServiceV2('demo-eshop-carts-service')

    t1 = threading.Thread(target=start_sqs_listener, args=(sqs_queue_url, cart_service_obj,))
    t1.start()

    cart_service_obj.add_endpoint(
        endpoint='/carts-service/healthCheck',
        endpoint_name='healthCheck',
        handler=health_check)

    cart_service_obj.add_endpoint(
        endpoint='/carts-service/createCart',
        endpoint_name='createCart',
        handler=create_cart,
        methods=['POST'])

    cart_service_obj.add_endpoint(
        endpoint='/carts-service/addToCart',
        endpoint_name='addToCart',
        handler=addToCart,
        methods=['PUT'])
    
    cart_service_obj.add_endpoint(
        endpoint='/carts-service/getCart',
        endpoint_name='getCart',
        handler=get_cart)

    cart_service_obj.add_endpoint(
        endpoint='/carts-service/removeFromCart',
        endpoint_name='removeFromCart',
        handler=removeFromCart,
        methods=['DELETE'])
    
    cart_service_obj.add_endpoint(
        endpoint='/carts-service/deleteCart',
        endpoint_name='deleteCart',
        handler=deleteCart,
        methods=['DELETE'])
    
    cart_service_obj.run("0.0.0.0", 8082)

    t1.join()


if __name__ == '__main__':
    main()