import os
import hashlib
import json
import uuid
import requests

from flask import request
from src.flask_service import FlaskService
from src.sqs import SqsClient
from time import sleep
from src.k8s_utils import get_service_endpoint

SQL_FILE = 'sql/shipping_schema.sql'


def health_check(**kwargs):
    if request.method != 'GET':
        return ('Invalid method', 400, {})

    try:
        return ('Health Check Success', 200, {})

    except Exception as e:
        return ('Internal Server Error', 500, {})
    

def get_unique_shipment_id():
    return uuid.uuid4().int


def create_shipment(**kwargs):
    try:
        shipment_id = get_unique_shipment_id()
        order_id = kwargs['order_id']
        user_id = kwargs['user_id']

        users_service_endpoint = get_service_endpoint('users-service', 'users-service')

        users_service_url = 'http://{}/users-service-internal/getUserAddress'.format(users_service_endpoint)

        resp = requests.get(users_service_url)

        resp_body = json.loads(resp.text)

        destination = resp_body['address']
        shipment_status = 'CREATED'  #CREATED, SHIPPED, DELIVERED

        query = "INSERT into shipping.shipments (shipment_id,order_id,user_id,destination,status) VALUES ({}, {}, {}, {}, {})".format(shipment_id, order_id, user_id, destination, shipment_status)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        kwargs["mysqlclientObj"].commit()

        return (json.dumps({'shipment_id': shipment_id, 'status': shipment_status}), 200, {'Content-Type': 'application/json'})
    except Exception as e:
        return ('Internal Server Error', 500, {})  


def update_shipment(**kwargs):
    try:
        if request.method != 'PUT':
            return ('Invalid method', 400, {})
        
        data = request.get_json(force=True)

        shipment_id = data['shipmentId']
        shipment_status = data['status']

        query = "UPDATE shipping.shipments SET status = {} WHERE shipment_id={}".format(shipment_status, shipment_id)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        kwargs["mysqlclientObj"].commit()


        # send SQS message to Ordering


        return (json.dumps({'shipment_id': shipment_id, 'status': shipment_status}), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        return ('Internal Server Error', 500, {})



def get_shipment_info(**kwargs):
    try:
        if request.method != 'GET':
            return ('Invalid method', 400, {})
        
        shipment_id = request.args.get('shipmentId')
        
        query = "SELECT * from shpipping.shipments where shipment_id={}".format(shipment_id)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        return (json.dumps(res), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        return ('Internal Server Error', 500, {})
    

def get_all_shipments(**kwargs):
    try:
        if request.method != 'GET':
            return ('Invalid method', 400, {})
        
        user_id = request.args.get('userId')
        
        query = "SELECT * from shpipping.shipments where user_id={}".format(user_id)

        res = kwargs["mysqlclientObj"].executeQuery(query)

        return (json.dumps(res), 200, {'Content-Type': 'application/json'})

    except Exception as e:
        return ('Internal Server Error', 500, {})


def start_sqs_listener(sqs_queue_url, shipping_service_obj):
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
                order_id = msg['order_id']
                user_id = msg['user_id']

                create_shipment(mysqlclientObj=shipping_service_obj.mysqlclientObj, user_id=user_id, order_id=order_id)
            else:
                #illegal messageType
                pass


def main():
    backend_db_info = {
        "endpoint": os.environ['RDS_MYSQL_ENDPOINT'],
        "port": os.environ['RDS_MYSQL_PORT'],
        "user": os.environ['RDS_MYSQL_USER'],
        "password": os.environ['RDS_MYSQL_PASSWORD'],
        "db_name": os.environ['RDS_MYSQL_DB_NAME']
    }

    users_service_obj = FlaskService(
        'demo-eshop-shipping-service', SQL_FILE, backend_db_info)

    users_service_obj.add_endpoint(
        endpoint='/shipping-service/updateShipment',
        endpoint_name='updateShipment',
        handler=update_shipment,
        methods=['PUT'])

    users_service_obj.add_endpoint(
        endpoint='/users-service/getShipmentInfo',
        endpoint_name='getShipmentInfo',
        handler=get_shipment_info)
    
    users_service_obj.add_endpoint(
        endpoint='/users-service/getAllShipments',
        endpoint_name='getAllShipments',
        handler=get_all_shipments)

    users_service_obj.add_endpoint(
        endpoint='/users-service/healthCheck',
        endpoint_name='healthCheck',
        handler=health_check)

    users_service_obj.run("0.0.0.0", 8084)


if __name__ == '__main__':
    main()