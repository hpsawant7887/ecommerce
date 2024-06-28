terraform {
  backend "s3" {
    bucket = "ecommerce-infra-state"
    key    = "backend/ecommerce.tfstate"
    region = "us-west-2"
    dynamodb_table = "ecommerce-tf-state"
    assume_role = {
      role_arn = "arn:aws:iam::507326814593:role/Admin_Role_Terraform"
    }
  }
}