CREATE DATABASE users;
CREATE TABLE  users.user_info (
    user_id int NOT NULL,
    username varchar(255),
    first_name varchar(255),
    last_name varchar(255),
    email varchar(255),
    user_address varchar(255),
    PRIMARY KEY (user_id)
);
CREATE TABLE users.credentials (
    user_id int NOT NULL,
    username varchar(255),
    md5_password varchar(255),
    PRIMARY KEY (user_id)
)