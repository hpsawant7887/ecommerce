data "aws_availability_zones" "availability_zones" {}

locals {

  availability_zones = [
    data.aws_availability_zones.availability_zones.names[0],
    data.aws_availability_zones.availability_zones.names[1]
  ]

  pri_subnet_cidr_map = {
    for k, v in zipmap(toset(var.private_subnet_cidr_list), local.availability_zones) :
      k => v
  }

  pub_subnet_cidr_map = {
    for k, v in zipmap(toset(var.public_subnet_cidr_list), local.availability_zones) :
      k => v
  }

}

module "network_setup" {
  source = "../modules/ecommerce_aws_networking"

  project_name = var.project_name
  cidr_block   = var.cidr_block
  public_subnet_cidrs = local.pub_subnet_cidr_map
  private_subnet_cidrs = local.pri_subnet_cidr_map

}

module "eks_cluster" {
  source = "../modules/ecommerce_eks"

  project_name = var.project_name
  subnet_id_list = module.network_setup.subnet_id_list
  eks_cluster_sg_id = module.network_setup.eks_cluster_sg
  eks_worker_sg_id = module.network_setup.eks_worker_nodes_sg
}

module "lb_for_eks" {
 source = "../modules/ecommerce_lb"

 vpc_id = module.network_setup.vpc_id
 public_subnet_id_list = module.network_setup.public_subnet_id_list
 project_name = var.project_name
 vpc_cidr_block = var.cidr_block
 root_domain_name = var.root_domain_name
 eks_nodes_asg_name = module.eks_cluster.eks_nodes_asg_name

}



