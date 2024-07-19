resource "aws_dynamodb_table" "carts" {
  name = "carts"
  billing_mode = "PROVISIONED"
  read_capacity = 10
  write_capacity = 5

  hash_key = "cart_id"
  
  attribute {
    name = "cart_id"
    type = "S"  # String data type
  }

  tags = {
    Name = "CartsTable"
  }
}

resource "aws_dynamodb_table" "orders" {
  name = "orders"
  billing_mode = "PROVISIONED"
  read_capacity = 10
  write_capacity = 5

  hash_key = "order_id"
 
  attribute {
    name = "order_id"
    type = "S"  # String data type
  }

  tags = {
    Name = "OrdersTable"
  }
}