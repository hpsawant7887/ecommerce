CREATE DATABASE onlinestore;
CREATE TABLE  onlinestore.owners (
    owner_id  int NOT NULL,
    first_name varchar(255),
    last_name varchar(255),
    PRIMARY KEY (owner_id)

);
CREATE TABLE onlinestore.store (
    store_id int NOT NULL,
    store_name varchar(255) NOT NULL,
    owner_id int NOT NULL,
    address varchar(255)
    PRIMARY KEY (store_id)
);

CREATE TABLE onlinestore.products (
    product_id int NOT NULL,
    product_name varchar(255) NOT NULL,
    store_id int NOT NULL,
    owner_id int NOT NULL,
    product_description varchar(255),
    price DECIMAL(10,2) NOT NULL,
    available_quantity int NOT NULL
    PRIMARY KEY (product_id)
)

