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
from src.otel_tracer import OtelTracer
from src.utils import DecimalEncoder
from time import sleep
from src.ecommerce_logger import set_logger
from prometheus_flask_exporter import PrometheusMetrics
from opentelemetry.instrumentation.logging import LoggingInstrumentor


APP_NAME = 'demo-eshop-carts-service'

otel_tracer_obj = OtelTracer(APP_NAME)

LoggingInstrumentor().instrument()
logger = set_logger()


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

@otel_tracer_obj.tracer.start_as_current_span('create_cart')
@verify_auth_header
def create_cart(**kwargs):
    if request.method != 'POST':
        return ('Invalid method', 400, {})
    try:
        data = request.get_json(force=True)
        user_id = int(data['userId'])
        dynamodbclient = kwargs['dynamodbclient']

        dynamodbclient.set_creds()

        cart_id = get_unique_cart_id()

        ddb_item = {
            'cart_id': cart_id,
            'user_id': user_id,
            'products': {}
        }

        status_code = dynamodbclient.create_dynamodb_item('carts', ddb_item)

        if status_code == 200:
            res = {
                'cart_id': cart_id,
                'user_id': user_id
            }
        
        else:
            logger.error('DynamoDB Error')
            return (json.dumps({}), 200, {})

        return (json.dumps(res), 200, {})
    
    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@otel_tracer_obj.tracer.start_as_current_span('get_cart')
@verify_auth_header
def get_cart(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})
    
    try:
        cart_id = request.args.get('cartId')
        user_id = int(request.args.get('userId'))

        dynamodbclient = kwargs['dynamodbclient']
        dynamodbclient.set_creds()

        primary_key = 'cart_id'
        key_value = cart_id
        secondary_key = 'user_id'
        secondary_key_value = user_id

        Key= {
            primary_key: key_value,
            secondary_key: secondary_key_value
        }

        res = dynamodbclient.get_dynamodb_item('carts', Key)

        return (json.dumps(res, cls=DecimalEncoder), 200, {})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@otel_tracer_obj.tracer.start_as_current_span('addToCart')
@verify_auth_header
def addToCart(**kwargs):
    if request.method != 'PUT':
        return ('Invalid method', 400, {})
    try:
        data = request.get_json(force=True)
        user_id = int(data['userId'])
        cart_id = data['cartId']
        product_id = data['productId']
        quantity = data['quantity']

        dynamodbclient = kwargs['dynamodbclient']
        dynamodbclient.set_creds()

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
            "#product_id": str(product_id)
        }
        ExpressionAttributeValues = {
            ":quantity": quantity
        }

        status_code = dynamodbclient.update_dynamodb_item('carts', Key, UpdateExpression, ExpressionAttributeValues, ExpressionAttributeNames)

        if status_code == 200:
            return (' {} added to Cart {}'.format(product_id, cart_id), 200, {})
        else:
            raise Exception('DynamoDB Error')

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@otel_tracer_obj.tracer.start_as_current_span('removeFromCart')
@verify_auth_header
def removeFromCart(**kwargs):
    try:
        data = request.get_json(force=True)
        cart_id = data['cartId']
        user_id = int(data['userId'])
        product_id = data['productId']

        dynamodbclient = kwargs['dynamodbclient']
        dynamodbclient.set_creds()

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
            "#product_id": str(product_id)
        }
        ExpressionAttributeValues = None

        status_code = dynamodbclient.update_dynamodb_item('carts', Key, UpdateExpression, ExpressionAttributeValues, ExpressionAttributeNames)

        if status_code == 200:
            return ('', 200, {})
        else:
            raise Exception('DynamoDB Error')

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@otel_tracer_obj.tracer.start_as_current_span('deleteCart')
@verify_auth_header
def deleteCart(**kwargs):
    try:
        data = request.get_json(force=True)
        cart_id = data['cartId']
        user_id = int(data['userId'])

        dynamodbclient = kwargs['dynamodbclient']
        dynamodbclient.set_creds()

        primary_key = 'cart_id'
        key_value = cart_id

        secondary_key = 'user_id'
        secondary_key_value = user_id

        Key= {
            primary_key: key_value,
            secondary_key: secondary_key_value
        }

        status_code = dynamodbclient.delete_dynamodb_item('carts', Key)

        if status_code == 200:
            return ('Cart {} for user_id {} deleted'.format(cart_id, user_id), 200, {})
        else:
            raise Exception('DynamoDB Error')

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


@verify_auth_header
def update_ddb(**kwargs):
    pass


def start_sqs_listener(sqs_queue_url, cart_service_obj):
    while True:
        try:
            sqs_client_obj = SqsClient()
            sqs_messages = sqs_client_obj.read_sqs_msg(sqs_queue_url)

            if 'Messages' not in sqs_messages or len(sqs_messages['Messages']) < 1:
                sleep(300)
                continue

            logger.info('Received SQS messages')

            for sqs_message in sqs_messages['Messages']:
                msg = json.loads(sqs_message['Body'])
                logger.info('SQS Message - {}'.format(msg))

                if msg['type'] == "NewOrderPlaced":
                    order = {
                        "order_id": msg['order_id'],
                        "cart_id": msg['cart_id'],
                        "user_id": msg['user_id']
                    }

                    cart_id = msg['cart_id']

                    primary_key = 'cart_id'
                    key_value = cart_id
                    secondary_key = 'user_id'
                    secondary_key_value = int(msg['user_id'])

                    Key= {
                        primary_key: key_value,
                        secondary_key: secondary_key_value
                    }

                    dynamodbclient = cart_service_obj.dynamodbclient
                    dynamodbclient.set_creds()

                    status_code = dynamodbclient.delete_dynamodb_item('carts', Key)

                    if status_code == 200:
                        logger.info('Sucessfully deleted cart')
                        sqs_client_obj.delete_sqs_msg(sqs_queue_url, sqs_message['ReceiptHandle'])
                else:
                    logger.error('Illegal SQS message Type in SQS message - {}'.format(msg))
                    sqs_client_obj.delete_sqs_msg(sqs_queue_url, sqs_message['ReceiptHandle'])
                    pass
        except Exception as e:
            logger.error(e)
            continue
            

def main():
    sqs_queue_url = os.environ['SQS_QUEUE_URL_ORDERING_TO_CARTS']

    cart_service_obj = FlaskServiceV2('demo-eshop-carts-service')
    metrics = PrometheusMetrics(cart_service_obj.service, default_labels={ 'service': APP_NAME })

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