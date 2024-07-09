
data "aws_secretsmanager_secret" "ecomm_rds_secret" {
  arn = var.rds_secret_arn
}

data "aws_secretsmanager_secret_version" "ecomm_rds_secret_version" {
  secret_id = data.aws_secretsmanager_secret.ecomm_rds_secret.id
}

resource "aws_rds_cluster" "ecomm_rds_cluster" {
  cluster_identifier = "ecomm-rds-cluster"
  engine             = "aurora-mysql"
  engine_mode        = "provisioned"
  engine_version     = "8.0.mysql_aurora.3.06.0"
#   engine_version     = "5.7.mysql_aurora.2.12.0"
  master_username    = jsondecode(data.aws_secretsmanager_secret_version.ecomm_rds_secret_version.secret_string)["ecomm_rds_admin_user"]
  master_password    = jsondecode(data.aws_secretsmanager_secret_version.ecomm_rds_secret_version.secret_string)["ecomm_rds_admin_password"]
  storage_encrypted  = false

  serverlessv2_scaling_configuration {
    max_capacity = 1.0
    min_capacity = 0.5
  }
  allow_major_version_upgrade = true
  skip_final_snapshot    = true
}

resource "aws_rds_cluster_instance" "ecomm_rds_cluster_instance" {
  cluster_identifier = aws_rds_cluster.ecomm_rds_cluster.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.ecomm_rds_cluster.engine
  engine_version     = aws_rds_cluster.ecomm_rds_cluster.engine_version
}