provider "aws" {
  assume_role {
    role_arn     = "arn:aws:iam::507326814593:role/Admin_Role_Terraform"
    session_name = "ecommerce_admin_session"
  }
  region = "us-west-2"
}