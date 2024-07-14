import os

from src.users_service import UserService, register_user_action, get_user_info, health_check


def main():
    backend_db_info = {
        "endpoint": os.environ['RDS_MYSQL_ENDPOINT'],
        "port": os.environ['RDS_MYSQL_PORT'],
        "user": os.environ['RDS_MYSQL_USER'],
        "password": os.environ['RDS_MYSQL_PASSWORD'],
        "db_name": os.environ['RDS_MYSQL_DB_NAME']
    }

    users_service_obj = UserService(
        'demo-eshop-users-service', backend_db_info)

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

    users_service_obj.run("0.0.0.0", 8080)


if __name__ == '__main__':
    main()
