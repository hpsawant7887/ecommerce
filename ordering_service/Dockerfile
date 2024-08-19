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
WORKDIR /opt/ordering_service

# Create Necessary Dirs
RUN mkdir -p /opt/ordering_service/bin
RUN mkdir -p /opt/ordering_service/src
RUN mkdir -p /opt/ordering_service/test

COPY setup.py /opt/ordering_service/
COPY bin/run_ordering_service.py /opt/ordering_service/bin/
COPY bin/__init__.py /opt/ordering_service/bin/
COPY src/flask_service_v2.py /opt/ordering_service/src/
COPY src/sqs.py /opt/ordering_service/src/
COPY src/dynamodb.py /opt/ordering_service/src/
COPY src/__init__.py /opt/ordering_service/src/
COPY src/k8s_utils.py /opt/carts_service/src/
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
RUN python3 setup.py install ordering_service

# Set container port
EXPOSE 8083

# Command for container
CMD [ "run-ordering-service" ]