resource "aws_dynamodb_table" "carts" {
  name = "carts"
  #billing_mode = "PROVISIONED"
  billing_mode = "PAY_PER_REQUEST"
  # read_capacity = 10
  # write_capacity = 5

  hash_key = "cart_id"
  range_key = "user_id"
  
  attribute {
    name = "cart_id"
    type = "S"  # String data type
  }

  attribute {
    name = "user_id"
    type = "N"
  }

  global_secondary_index {
    name            = "gsi-carts"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  tags = {
    Name = "CartsTable"
  }
}

resource "aws_dynamodb_table" "orders" {
  name = "orders"
  # billing_mode = "PROVISIONED"
  # read_capacity = 10
  # write_capacity = 5
  billing_mode = "PAY_PER_REQUEST"

  hash_key = "order_id"
  range_key = "user_id"
 
  attribute {
    name = "order_id"
    type = "S"  # String data type
  }

  attribute {
    name = "user_id"
    type = "N"
  }

  global_secondary_index {
    name            = "gsi-orders"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  tags = {
    Name = "OrdersTable"
  }
}

resource "aws_vpc_endpoint" "dynamodb_endpoint" {
  vpc_id = var.vpc_id
  service_name = "com.amazonaws.${var.region}.dynamodb"
  route_table_ids = var.route_table_ids
}