import os
import threading
import json
import logging
import hashlib
import uuid
import requests

from flask import request
from src.flask_service_v2 import FlaskServiceV2
from src.k8s_utils import get_service_endpoint
from src.sqs import SqsClient
from src.utils import DecimalEncoder
from time import sleep

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def get_unique_order_id():
    return uuid.uuid4().hex


def health_check(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})

    try:
        return ('Health Check Success', 200, {})

    except Exception as e:
        logger.error(e)
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
            logger.error(e)
            return ('Internal Server Error', 500, {})

    return wrapper


@verify_auth_header
def placeOrder(**kwargs):
    if request.method != "POST":
        return ('Invalid Method', 400, {})
    
    try:
        data = request.get_json(force=True)
        cart_id = data['cartId']
        user_id = data['userId']


        order_id = get_unique_order_id()

        dynamodbclient = kwargs['dynamodbclient']

        primary_key = 'cart_id'
        key_value = cart_id
        secondary_key = 'user_id'
        secondary_key_value = user_id

        Key= {
            primary_key: key_value,
            secondary_key: secondary_key_value
        }

        # get all products from cart
        cart_item = dynamodbclient.get_dynamodb_item('carts', Key)

        products = cart_item['products']

        # create dynamodb record in orders table

        ddb_item = {
            'order_id': order_id,
            'cart_id': cart_id,
            'user_id': user_id,
            'products': products,
            'status': 'Pending'
        }

        ddb_res = dynamodbclient.create_dynamodb_item('orders', ddb_item)

        # create SQS client
        sqs_client_obj = SqsClient()

        sqs_msg = {
            'type': 'NewOrderPlaced',
            'order_id': order_id,
            'cart_id': cart_id,
            'user_id': user_id,
            'products': products,
        }

        # send sqs message to Shipping
        sqs_queue_url = os.environ['SQS_QUEUE_URL_ORDERING_TO_SHIPPING']
        sqs_client_obj.send_sqs_msg(sqs_queue_url, sqs_msg)

        # send sqs message to OnlineStore
        sqs_queue_url = os.environ['SQS_QUEUE_URL_ORDERING_TO_ONLINESTORE']
        sqs_client_obj.send_sqs_msg(sqs_queue_url, sqs_msg)

        # send sqs message to delete the cart
        sqs_queue_url = os.environ['SQS_QUEUE_URL_ORDERING_TO_CARTS']
        sqs_client_obj.send_sqs_msg(sqs_queue_url, sqs_msg)

        # return ddb response
        return (json.dumps(ddb_res), 200, {})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})
    

def updateOrderStatus(**kwargs):
    pass


@verify_auth_header
def getOrderStatus(**kwargs):
    if request.method != "GET":
        return ('Invalid Method', 400, {})
    
    try:
        user_id = request.args.get('userId')
        order_id = request.args.get('orderId')

        dynamodbclient = kwargs['dynamodbclient']

        primary_key = 'order_id'
        key_value = order_id
        secondary_key = 'user_id'
        secondary_key_value = user_id

        Key= {
            primary_key: key_value,
            secondary_key: secondary_key_value
        }

        res = dynamodbclient.get_dynamodb_item('orders', Key)

        return (json.dumps(res, cls=DecimalEncoder), 200, {})

    except Exception as e:
        logger.error(e)
        return ('Internal Server error', 500, {})
    

def start_sqs_listener(sqs_queue_url, ordering_service_obj):
    sqs_client_obj = SqsClient()

    while True:
        try:
            sqs_messages = sqs_client_obj.read_sqs_msg(sqs_queue_url)

            if 'Messages' not in sqs_messages or len(sqs_messages['Messages']) < 1:
                sleep(300)
                continue

            for sqs_message in sqs_messages['Messages']:
                msg = json.loads(sqs_message['Body'])
                sqs_client_obj.delete_sqs_msg(sqs_queue_url, sqs_message['ReceiptHandle'])

                if msg['type'] == "OrderShipped" or msg['type'] == "OrderDelivered":
                    order = {
                        "order_id": msg['order_id'],
                        "status": msg['shipment_status']
                    }
                    dynamodbclient = ordering_service_obj.dynamodbclient

                    #update order status in dynamodb
                    Key = {
                        'order_id': order['order_id']
                    }

                    UpdateExpression = 'SET #status = :order_status'

                    ExpressionAttributeNames = {
                        "#status": "status"
                    }
            
                    ExpressionAttributeValues = {
                        ":order_status": order['status']
                    }

                    res = dynamodbclient.update_dynamodb_item('orders', Key, UpdateExpression, ExpressionAttributeValues, ExpressionAttributeNames)

                else:
                    #illegal messageType
                    logger.error('Illegal message type {}'.format(msg['type']))
                    pass
        except Exception as e:
            logger.error(e)
            continue

def main():
    sqs_queue_url = os.environ['SQS_QUEUE_URL_SHIPPING_TO_ORDERING']

    ordering_service_obj = FlaskServiceV2('demo-eshop-ordering-service')

    t1 = threading.Thread(target=start_sqs_listener, args=(sqs_queue_url, ordering_service_obj,))
    t1.start()

    ordering_service_obj.add_endpoint(
        endpoint='/ordering-service/healthCheck',
        endpoint_name='healthCheck',
        handler=health_check)

    ordering_service_obj.add_endpoint(
        endpoint='/ordering-service/placeOrder',
        endpoint_name='placeOrder',
        handler=placeOrder,
        methods=['POST'])
    
    ordering_service_obj.add_endpoint(
        endpoint='/ordering-service/getOrderStatus',
        endpoint_name='getOrderStatus',
        handler=getOrderStatus)
    
    
    ordering_service_obj.run("0.0.0.0", 8083)

    t1.join()


if __name__ == '__main__':
    main()