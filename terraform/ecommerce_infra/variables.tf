variable "cidr_block" {
 type        = string
 description = "CIDR Block for VPC"
}

# variable "public_subnet_cidr" {
#  type        = string
#  description = "Public Subnet CIDR value"
# }
 
variable "private_subnet_cidr_list" {
 type        = list(string)
 description = "list of private subnet cidrs"
}

variable "project_name" {
 type        = string
 description = "Name of the Project"
}

variable "root_domain_name" {
  type    = string
  description = "root domain name"
}

variable "public_subnet_cidr_list" {
 type        = list(string)
 description = "list of private subnet cidrs"
}

variable "rds_private_subnet_cidrs_list" {
 type        = list(string)
 description = "RDS private subnet CIDRs"
}

