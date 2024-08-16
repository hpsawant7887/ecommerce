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

variable "route_table_ids" {
  type        = list(string)
  description = "list of route table ids"

}