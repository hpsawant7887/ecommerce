CREATE DATABASE shipping;
CREATE TABLE  shipping.shipments (
    shipment_id bigint NOT NULL,
    order_id varchar(255) NOT NULL,
    user_id bigint NOT NULL,
    destination varchar(255) NOT NULL,
    status varchar(255) NOT NULL,
    PRIMARY KEY (shipment_id)
);