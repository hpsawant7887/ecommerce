
data "aws_secretsmanager_secret" "ecomm_rds_secret" {
  arn = var.rds_secret_arn
}

data "aws_secretsmanager_secret_version" "ecomm_rds_secret_version" {
  secret_id = data.aws_secretsmanager_secret.ecomm_rds_secret.id
}

resource "aws_subnet" "rds_private_subnet" {
  for_each = var.rds_private_subnet_cidrs

  vpc_id             = var.vpc_id
  cidr_block         = each.key
  availability_zone  = each.value
  map_public_ip_on_launch = false
}


resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "rds_subnet_group"
  subnet_ids = [for subnet in aws_subnet.rds_private_subnet: subnet.id]

  tags = {
    Name = "RDS Subnet Group"
  }
}


resource "aws_security_group" "rds_sg" {
  name = "rds-sg"
  vpc_id =  var.vpc_id

  ingress {
    from_port = 3306
    to_port = 3306
    protocol = "tcp"
    cidr_blocks = var.ingress_cidr_list

  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]

    }
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
  db_subnet_group_name = aws_db_subnet_group.rds_subnet_group.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
}

resource "aws_rds_cluster_instance" "ecomm_rds_cluster_instance" {
  cluster_identifier = aws_rds_cluster.ecomm_rds_cluster.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.ecomm_rds_cluster.engine
  engine_version     = aws_rds_cluster.ecomm_rds_cluster.engine_version
  db_subnet_group_name = aws_db_subnet_group.rds_subnet_group.name
  publicly_accessible = false
}
