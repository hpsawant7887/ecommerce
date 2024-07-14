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
WORKDIR /opt/users_service

# Create Necessary Dirs
RUN mkdir -p /opt/users_service/bin
RUN mkdir -p /opt/users_service/src
RUN mkdir -p /opt/users_service/test
RUN mkdir -p /opt/users_service/sql

COPY setup.py /opt/users_service/
COPY bin/run_users_service.py /opt/users_service/bin/
COPY bin/__init__.py /opt/users_service/bin/
COPY src/users_service.py /opt/users_service/src/
COPY src/mysqlclient.py /opt/users_service/src/
COPY src/__init__.py /opt/users_service/src/
COPY sql/user_schema.sql /opt/users_service/sql/
#COPY test/test_users.py /opt/users_service/test/

# Install dependencies
RUN pip install setuptools
RUN pip install pytest
RUN pip install pymysql
RUN pip install flask

# Setup the Users Service
RUN python3 setup.py install users_service

# Set container port
EXPOSE 8080

# Command for container
CMD [ "run-users-service" ]