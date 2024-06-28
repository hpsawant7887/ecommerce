variable "project_name" {
 type        = string
 description = "Name of the Project"
}

variable "subnet_id_list" {
  type        = list(string)
  description =  "AWS Subnet ID list"
}