#BASE IMAGE
FROM python:3.9-slim

RUN apt-get update && apt-get install -y xvfb
RUN apt-get install -y unzip
RUN apt-get install -y wget
RUN apt-get install -y gnupg

# Install Tools and Utils
RUN apt-get update -y
RUN apt-get install -y vim
RUN apt-get install -y cron
RUN apt-get install -y iputils-ping
RUN apt-get install -y dnsutils
RUN apt-get install -y curl
RUN apt-get install -y procps

# Set Working Directory in the container
WORKDIR /opt/shipping_service

# Create Necessary Dirs
RUN mkdir -p /opt/shipping_service/bin
RUN mkdir -p /opt/shipping_service/src
RUN mkdir -p /opt/shipping_service/test
RUN mkdir -p /opt/shipping_service/sql

COPY setup.py /opt/shipping_service/
COPY bin/run_shipping_service.py /opt/shipping_service/bin/
COPY bin/__init__.py /opt/shipping_service/bin/
COPY src/flask_service.py /opt/shipping_service/src/
COPY src/mysqlclient.py /opt/shipping_service/src/
COPY src/sqs.py /opt/shipping_service/src/
COPY src/__init__.py /opt/shipping_service/src/
COPY sql/shipping_schema.sql /opt/shipping_service/sql/
COPY src/k8s_utils.py /opt/shipping_service/src/
COPY src/utils.py /opt/shipping_service/src/
#COPY test/test_users.py /opt/users_service/test/

# Install dependencies
RUN pip install setuptools
RUN pip install pytest
RUN pip install pymysql
RUN pip install flask
RUN pip install boto3
RUN pip install requests
RUN pip install kubernetes

# Setup the Users Service
RUN python3 setup.py install shipping_service

# Set container port
EXPOSE 8084

# Command for container
CMD [ "run-shipping-service" ]