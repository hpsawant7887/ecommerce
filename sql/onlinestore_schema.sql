CREATE DATABASE onlinestore;
CREATE TABLE onlinestore.products (
    product_id int NOT NULL,
    product_name varchar(255) NOT NULL,
    product_description varchar(255),
    price DECIMAL(10,2) NOT NULL,
    available_quantity int NOT NULL,
    PRIMARY KEY (product_id)
)

