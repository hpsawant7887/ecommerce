variable "rds_secret_arn" {
 type        = string
 description = "ARN of RDS secret in AWS Secret Manager"
}

variable "rds_private_subnet_cidrs" {
 type        = map(string)
 description = "RDS private subnet CIDRs"
}

variable "vpc_id" {
 type        = string
 description = "VPC ID in which RDS is to be launched"
}

variable "ingress_cidr_list" {
 type        = list(string)
 description = "ingress cidr list for rds"
}