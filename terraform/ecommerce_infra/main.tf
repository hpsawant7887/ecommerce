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

}

module "network_setup" {
  source = "../modules/ecommerce_aws_networking"

  project_name = var.project_name
  cidr_block   = var.cidr_block
  public_subnet_cidr = var.public_subnet_cidr
  private_subnet_cidrs = local.pri_subnet_cidr_map

}

module "eks_cluster" {
  source = "../modules/ecommerce_eks"

  project_name = var.project_name
  subnet_id_list = module.network_setup.subnet_id_list
  
}

