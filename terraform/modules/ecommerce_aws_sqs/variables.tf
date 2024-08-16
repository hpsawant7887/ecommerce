variable "sqs_queue_name_list" {
 type        = list(string)
 description = "AWS SQS Queue name list"
}

variable "vpc_id" {
 type        = string
 description = "VPC ID for SQS VPC endpoint"
}

variable "region" {
 type        = string
 description = "AWS region"
}

variable "sg_id" {
 type        = string
 description = "SG for VPC endpoint"
}

variable "subnet_id_list" {
  type        = list(string)
  description =  "AWS Subnet ID list"
}