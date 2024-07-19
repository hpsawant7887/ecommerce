resource "aws_sqs_queue" "ordering_to_shipping" {
  name                      = "ordering-to-shipping"
  delay_seconds             = 90
  message_retention_seconds = 900
  receive_wait_time_seconds = 10
}

resource "aws_sqs_queue" "ordering_to_onlinestore" {
  name                      = "ordering-to-onlinestore"
  delay_seconds             = 90
  message_retention_seconds = 900
  receive_wait_time_seconds = 10
}


resource "aws_sqs_queue" "shipping_to_ordering" {
  name                      = "shipping-to-ordering"
  delay_seconds             = 90
  message_retention_seconds = 900
  receive_wait_time_seconds = 10
}