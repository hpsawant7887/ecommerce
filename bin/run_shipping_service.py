import os
import threading
import hashlib
import json
import logging
import uuid
import requests

from flask import request
from src.flask_service import FlaskService
from src.otel_tracer import OtelTracer
from src.sqs import SqsClient
from time import sleep
from src.k8s_utils import get_service_endpoint
from src.utils import DecimalEncoder
from src.ecommerce_logger import set_logger
from prometheus_flask_exporter import PrometheusMetrics

SQL_FILE = 'sql/shipping_schema.sql'
APP_NAME = 'demo-eshop-shipping-service'

otel_tracer_obj = OtelTracer(APP_NAME)
logger = set_logger()

def health_check(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})

    try:
        return ('Health Check Success', 200, {})

    except Exception as e:
        return ('Internal Server Error', 500, {})
    

def get_unique_shipment_id():
    return uuid.uuid4().int


@otel_tracer_obj.tracer.start_as_current_span('create_shipment')
def create_shipment(**kwargs):
    try:
        shipment_id = get_unique_shipment_id()
        order_id = kwargs['order_id']
        user_id = int(kwargs['user_id'])

        users_service_endpoint = get_service_endpoint('demo-eshop-users-service', 'users-service')

        users_service_url = 'http://{}/users-service-internal/getUserAddress?userId={}'.format(users_service_endpoint, user_id)

        resp = requests.get(users_service_url)

        resp_body = json.loads(resp.text)

        destination = resp_body['address']
        shipment_status = 'CREATED'  #CREATED, SHIPPED, DELIVERED

        kwargs["mysqlclientObj"].setConnection()

        query = "INSERT into shipping.shipments (shipment_id,order_id,user_id,destination,status) VALUES ({},'{}',{},'{}','{}')".format(shipment_id, order_id, user_id, destination, shipment_status)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        kwargs["mysqlclientObj"].commit()

        return True
    except Exception as e:
        logger.error(e)
        return False


@otel_tracer_obj.tracer.start_as_current_span('update_shipment')
def update_shipment(**kwargs):
    try:
        if request.method != 'PUT':
            return ('Invalid method', 400, {})
        
        data = request.get_json(force=True)

        shipment_id = int(data['shipmentId'])
        shipment_status = data['status']

        if shipment_status == 'SHIPPED':
            msg_type = "OrderShipped"
        elif shipment_status == 'DELIVERED':
            msg_type = "OrderDelivered"
        else:
            raise Exception('Incorrect shipment status {}'.format(shipment_status))

        kwargs["mysqlclientObj"].setConnection()

        query = "UPDATE shipping.shipments SET status = '{}' WHERE shipment_id={}".format(shipment_status, shipment_id)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        kwargs["mysqlclientObj"].commit()

        get_shipment_query = "SELECT shipment_id, user_id, order_id, status FROM shipping.shipments WHERE shipment_id={}".format(shipment_id)

        res = kwargs["mysqlclientObj"].executeQuery(get_shipment_query)[0]

        # send SQS message to Ordering
        sqs_client_obj = SqsClient()
        sqs_queue_url = os.environ['SQS_QUEUE_URL_SHIPPING_TO_ORDERING']

        sqs_msg = {
            'type': msg_type,
            'shipment_id': res[0],
            'user_id': res[1],
            'order_id': res[2],
            'shipment_status': res[3]
        }

        sqs_client_obj.send_sqs_msg(sqs_queue_url, json.dumps(sqs_msg, cls=DecimalEncoder))

        kwargs["mysqlclientObj"].closeConnection()

        return (json.dumps({'shipment_id': shipment_id, 'status': shipment_status}), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})



@otel_tracer_obj.tracer.start_as_current_span('get_shipment_info')
def get_shipment_info(**kwargs):
    try:
        if request.method != 'GET':
            return ('Invalid method', 400, {})
        
        shipment_id = int(request.args.get('shipmentId'))

        kwargs["mysqlclientObj"].setConnection()
        
        query = "SELECT * from shpipping.shipments where shipment_id={}".format(shipment_id)

        res = kwargs["mysqlclientObj"].executeQuery(query)[0]

        kwargs["mysqlclientObj"].closeConnection()

        shipment_info = {
            "shipment_id": res[0],
            "order_id": res[1],
            "user_id": res[2],
            "shipment_destination": res[3],
            "shipment_status": res[4]
        }

        return (json.dumps(shipment_info, cls=DecimalEncoder), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})
    

@otel_tracer_obj.tracer.start_as_current_span('get_all_shipments')
def get_all_shipments(**kwargs):
    try:
        if request.method != 'GET':
            return ('Invalid method', 400, {})
        
        user_id = int(request.args.get('userId'))

        kwargs["mysqlclientObj"].setConnection()
        
        query = "SELECT shipment_id,order_id,user_id,status from shipping.shipments where user_id={}".format(user_id)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        kwargs["mysqlclientObj"].closeConnection()

        shipments = {'shipments': []}

        for shipment in res:
            s = {}
            s['shipmentId'] = shipment[0]
            s['orderId'] = shipment[1]
            s['userId'] = shipment[2]
            s['shipment_status'] = shipment[3]

            shipments['shipments'].append(s)

        return (json.dumps(shipments, cls=DecimalEncoder), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        logger.error(e)
        return ('Internal Server Error', 500, {})


def start_sqs_listener(sqs_queue_url, shipping_service_obj):
    sqs_client_obj = SqsClient()

    while True:
        try:
            sqs_messages = sqs_client_obj.read_sqs_msg(sqs_queue_url)

            if 'Messages' not in sqs_messages or len(sqs_messages['Messages']) < 1:
                sleep(300)
                continue

            logger.info('Received SQS messages')

            for sqs_message in sqs_messages['Messages']:
                msg = json.loads(sqs_message['Body'])
                logger.info('SQS Message - {}'.format(msg))

                if msg['type'] == "NewOrderPlaced":
                    order_id = msg['order_id']
                    user_id = msg['user_id']

                    r = create_shipment(mysqlclientObj=shipping_service_obj.mysqlclient, user_id=user_id, order_id=order_id)
                    if r:
                        sqs_client_obj.delete_sqs_msg(sqs_queue_url, sqs_message['ReceiptHandle'])
                else:
                    #illegal messageType
                    pass
        except Exception as e:
            logger.error(e)
            continue


def main():
    backend_db_info = {
        "endpoint": os.environ['RDS_MYSQL_ENDPOINT'],
        "port": os.environ['RDS_MYSQL_PORT'],
        "user": os.environ['RDS_MYSQL_USER'],
        "password": os.environ['RDS_MYSQL_PASSWORD'],
        "db_name": os.environ['RDS_MYSQL_DB_NAME']
    }

    sqs_queue_url = os.environ['SQS_QUEUE_URL_ORDERING_TO_SHIPPING']

    shipping_service_obj = FlaskService(
        APP_NAME, SQL_FILE, backend_db_info)
    
    metrics = PrometheusMetrics(shipping_service_obj.service, default_labels={ 'service': APP_NAME })
    
    t1 = threading.Thread(target=start_sqs_listener, args=(sqs_queue_url, shipping_service_obj,))
    t1.start()

    shipping_service_obj.add_endpoint(
        endpoint='/shipping-service/updateShipment',
        endpoint_name='updateShipment',
        handler=update_shipment,
        methods=['PUT'])

    shipping_service_obj.add_endpoint(
        endpoint='/shipping-service/getShipmentInfo',
        endpoint_name='getShipmentInfo',
        handler=get_shipment_info)
    
    shipping_service_obj.add_endpoint(
        endpoint='/shipping-service/getAllShipments',
        endpoint_name='getAllShipments',
        handler=get_all_shipments)

    shipping_service_obj.add_endpoint(
        endpoint='/shipping-service/healthCheck',
        endpoint_name='healthCheck',
        handler=health_check)

    shipping_service_obj.run("0.0.0.0", 8084)


if __name__ == '__main__':
    main()