CREATE DATABASE shipping;
CREATE TABLE  shipping.shipments (
    shipment_id int NOT NULL,
    order_id int NOT NULL,
    user_id int NOT NULL,
    destination varchar(255) NOT NULL,
    status varchar(255) NOT NULL,
    PRIMARY KEY (shipment_id)
);