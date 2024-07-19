import os
import threading
import json

from src.onlinestore_service import OnlineStoreService, decrease_product_count, health_check, get_product, search_products, create_owner, add_product, add_store, get_store_info, getStores
from src.sqs import SqsClient
from time import sleep


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
                    decrease_product_count(mysqlclientObj=onlinestore_service_obj.mysqlclientObj, product_id=product_id, quantity=quantity)

                onlinestore_service_obj.mysqlclientObj.commit()
            else:
                #illegal messageType
                pass

def main():
    backend_db_info = {
        "endpoint": os.environ['RDS_MYSQL_ENDPOINT'],
        "port": os.environ['RDS_MYSQL_PORT'],
        "user": os.environ['RDS_MYSQL_USER'],
        "password": os.environ['RDS_MYSQL_PASSWORD'],
        "db_name": os.environ['RDS_MYSQL_DB_NAME'],
        "auth_db_name": os.environ['RDS_MYSQL_AUTH_DB_NAME']
    }

    sqs_queue_url = os.environ['SQS_QUEUE_URL_ORDERING_TO_ONLINE_STORE']

    onlinestore_service_obj = OnlineStoreService('demo-eshop-online-store-service',backend_db_info)

    t1 = threading.Thread(target=start_sqs_listener, args=(sqs_queue_url, onlinestore_service_obj,))
    t1.start()
    t1.join()

    onlinestore_service_obj.add_endpoint(
        endpoint='/online-store/healthCheck',
        endpoint_name='healthCheck',
        handler=health_check)

    onlinestore_service_obj.add_endpoint(
        endpoint='/online-store/searchProducts',
        endpoint_name='searchProducts',
        handler=search_products)

    onlinestore_service_obj.add_endpoint(
        endpoint='/online-store/getProductInfo',
        endpoint_name='getProductInfo',
        handler=get_product)

    onlinestore_service_obj.add_endpoint(
        endpoint='/online-store/createStoreOwner',
        endpoint_name='createStoreOwner',
        handler=create_owner,
        methods=['POST'])
    
    onlinestore_service_obj.add_endpoint(
        endpoint='/online-store/addStore',
        endpoint_name='addStore',
        handler=add_store,
        methods=['POST'])
    
    onlinestore_service_obj.add_endpoint(
        endpoint='/online-store/addProduct',
        endpoint_name='addProduct',
        handler=add_product,
        methods=['POST'])
    
    onlinestore_service_obj.add_endpoint(
        endpoint='/online-store/getStoreInfo',
        endpoint_name='getStoreInfo',
        handler=get_store_info)
    
    onlinestore_service_obj.getStores(
        endpoint='/online-store/getStores',
        endpoint_name='getStores',
        handler=getStores)
    
    onlinestore_service_obj.run("0.0.0.0", 8081)
    

if __name__ == '__main__':
    main()