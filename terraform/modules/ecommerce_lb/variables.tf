variable "vpc_id" {
 type        = string
 description = "VPC ID"
}

variable "subnet_id_list" {
  type        = list(string)
  description =  "AWS Subnet ID list"
}

variable "project_name" {
 type        = string
 description = "Name of the Project"
}

variable "vpc_cidr_block" {
 type        = string
 description = "CIDR Block for VPC"
}

variable "eks_nodes_asg_name" {
    type = string
    description = "EKS Node Group ASG Name"
}

variable "root_domain_name" {
  type    = string
  description = "Root Domain Name"
}