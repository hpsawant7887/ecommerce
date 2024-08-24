import os
import hashlib
import json
import logging
import uuid

from flask import request
from src.flask_service import FlaskService

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

SQL_FILE = 'sql/user_schema.sql'


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

        # Generate 64 bit unique id
        user_id = uuid.uuid1().int >> 64

        user_info_query = """INSERT into users.user_info (user_id, username, first_name, \
            last_name, email, user_address) values ({},'{}','{}','{}','{}','{}')""".format(
            user_id, username, first_name, last_name, email, address)

        mysqlclientObj.executeQuery(user_info_query)

        user_creds_query = """INSERT into users.credentials (user_id, md5_password) values ({},'{}')""".format(user_id, password)

        mysqlclientObj.executeQuery(user_creds_query)

        mysqlclientObj.commit()

        return ('User Registration Complete', 200, {})

    except Exception as e:
        # return error
        logging.error(e)
        return ('Internal Server Error', 500, {})


def health_check(**kwargs):
    if request.method != 'GET':
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
            
            get_password_query = "SELECT credentials.md5_password FROM credentials JOIN user_info ON credentials.user_id = user_info.user_id  WHERE user_info.username = '{}'".format(request.authorization.username)

            # get_password_query = "SELECT md5_password from users.credentials WHERE username='{}'".format(
            #     request.authorization.username)

            stored_password = mysqlclientObj.executeQuery(get_password_query)[
                0][0]

            if stored_password != hashlib.md5(
                    request.authorization.password.encode('utf-8')).hexdigest():
                return ('Authentication Failed', 401, {})

            return func(mysqlclientObj)
        except Exception as e:
            logging.error(e)
            return ('Internal Server Error', 500, {})

    return wrapper


@verify_auth_header
def get_user_info(mysqlclientObj):
    user_info_query = "SELECT user_id, username, first_name, last_name, email, address from users.user_info WHERE username='{}'".format(
        request.authorization.username)

    res = mysqlclientObj.executeQuery(user_info_query)

    return (json.dumps(res), 200, {'Content-Type': 'application/json'})


def get_user_address(mysqlclientObj):
    try:
        user_id = request.args.get('userId')

        user_info_query = "SELECT first_name, last_name, address from users.user_info WHERE user_id='{}'".format(user_id)

        res = mysqlclientObj.executeQuery(user_info_query)[0]

        address_info = {
            'first_name': res[0],
            'last_name': res[1],
            'address': res[2]
        }

        return (json.dumps(address_info), 200, {'Content-Type': 'application/json'})
    except Exception as e:
        logging.error(e)


def verify_user(mysqlclientObj):
    try:
        data = request.get_json(force=True)

        if not data:
            return ('Invalid Request Body', 400, {})
        
        username = data['username']
        password = hashlib.md5(data['password'].encode('utf-8')).hexdigest()

        get_password_query = "SELECT credentials.md5_password FROM credentials JOIN user_info ON credentials.user_id = user_info.user_id  WHERE user_info.username = '{}'".format(username)

        stored_password = mysqlclientObj.executeQuery(get_password_query)[0][0]

        if stored_password != password:
            return ('Incorrect Credentials', 401, {})
            
        return ('User Verified', 200, {})
        
    except Exception as e:
        logging.error(e)
        return ('Internal Server Error', 500, {})



def main():
    backend_db_info = {
        "endpoint": os.environ['RDS_MYSQL_ENDPOINT'],
        "port": os.environ['RDS_MYSQL_PORT'],
        "user": os.environ['RDS_MYSQL_USER'],
        "password": os.environ['RDS_MYSQL_PASSWORD'],
        "db_name": os.environ['RDS_MYSQL_DB_NAME']
    }

    users_service_obj = FlaskService(
        'demo-eshop-users-service', SQL_FILE, backend_db_info)

    users_service_obj.add_endpoint(
        endpoint='/users-service/register_user',
        endpoint_name='userRegistration',
        handler=register_user_action,
        methods=['POST'])

    users_service_obj.add_endpoint(
        endpoint='/users-service/getUserInfo',
        endpoint_name='getUserInfo',
        handler=get_user_info)

    users_service_obj.add_endpoint(
        endpoint='/users-service/healthCheck',
        endpoint_name='healthCheck',
        handler=health_check)
    
    users_service_obj.add_endpoint(
        endpoint='/users-service-internal/verify_user',
        endpoint_name='verify_user',
        handler=verify_user,
        methods=['POST'])
    
    users_service_obj.add_endpoint(
        endpoint='/users-service-internal/getUserAddress',
        endpoint_name='getUserAddress',
        handler=get_user_address)

    users_service_obj.run("0.0.0.0", 8080)


if __name__ == '__main__':
    main()
