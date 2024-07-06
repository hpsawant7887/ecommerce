variable "project_name" {
 type        = string
 description = "Name of the Project"
}

variable "subnet_id_list" {
  type        = list(string)
  description =  "AWS Subnet ID list"
}

variable "eks_cluster_sg_id" {
  type        = string
  description = "SG for eks control plane"
}

variable "eks_worker_sg_id" {
  type        = string
  description = "SG for worker nodes"
}