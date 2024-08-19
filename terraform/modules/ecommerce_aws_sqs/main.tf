resource "aws_sqs_queue" "ecomm_sqs_queue" {
  for_each = toset(var.sqs_queue_name_list)

  name                      = each.key
  delay_seconds             = 90
  message_retention_seconds = 900
  receive_wait_time_seconds = 10

}

resource "aws_vpc_endpoint" "sqs_endpoint" {
  vpc_id = var.vpc_id
  service_name = "com.amazonaws.${var.region}.sqs"
  vpc_endpoint_type = "Interface"
  subnet_ids        = var.subnet_id_list
  private_dns_enabled = true
  security_group_ids = [var.sg_id]
}