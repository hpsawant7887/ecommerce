project_name = "ecommerce-service"
cidr_block = "10.0.0.0/16"
public_subnet_cidr_list = ["10.0.1.0/24", "10.0.4.0/24"]
private_subnet_cidr_list = ["10.0.2.0/24", "10.0.3.0/24"]
root_domain_name = "demo-eshop.com"
rds_private_subnet_cidrs_list = ["10.0.5.0/24", "10.0.6.0/24"]
sqs_queue_name_list = ["ordering-to-shipping", "ordering-to-onlinestore", "shipping-to-ordering", "carts-to-ordering", "ordering-to-carts"]