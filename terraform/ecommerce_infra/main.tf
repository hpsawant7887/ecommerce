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

  rds_subnet_cidr_map = {
    for k, v in zipmap(toset(var.rds_private_subnet_cidrs_list), local.availability_zones) :
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

data "aws_secretsmanager_secret" "rds_secret" {
  name = "ecomm_rds_secret"
}

module "rds" {
  source = "../modules/ecommerce_aws_rds"

  rds_secret_arn = data.aws_secretsmanager_secret.rds_secret.arn
  rds_private_subnet_cidrs = local.rds_subnet_cidr_map
  vpc_id = module.network_setup.vpc_id
  ingress_cidr_list = var.private_subnet_cidr_list
}

module "dynamodb" {
  source = "../modules/ecommerce_aws_dynamodb"

  vpc_id = module.network_setup.vpc_id
  region = "us-west-2"
  sg_id = module.network_setup.eks_worker_nodes_sg
  route_table_ids = concat(module.network_setup.private_subnet_route_table_id_list, module.network_setup.public_subnet_route_table_id_list)
  }

module "sqs" {
  source = "../modules/ecommerce_aws_sqs"

  sqs_queue_name_list = var.sqs_queue_name_list
  vpc_id = module.network_setup.vpc_id
  region = "us-west-2"
  sg_id = module.network_setup.eks_worker_nodes_sg
}



