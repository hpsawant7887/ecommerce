variable "cidr_block" {
 type        = string
 description = "CIDR Block for VPC"
}

variable "public_subnet_cidrs" {
 type        = map(string)
 description = "Public Subnet CIDR value"
}
 
variable "private_subnet_cidrs" {
 type        = map(string)
 description = "map of private subnet cidrs to availability zones"
}

variable "project_name" {
 type        = string
 description = "Name of the Project"
}