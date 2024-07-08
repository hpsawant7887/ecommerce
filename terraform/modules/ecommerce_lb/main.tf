
resource "aws_security_group" "allow_http_https" {
  name        = "dev_allow_tls"
  description = "Allow HTTP/TLS inbound traffic"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "all"
    from_port   = 0
    to_port     = 0
    protocol    = "all"
    cidr_blocks = [var.vpc_cidr_block]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "alb-sg"
  }
}

resource "aws_lb" "alb_for_eks" {
  name               = "${var.project_name}-eks-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.allow_http_https.id]
  subnets            = var.public_subnet_id_list

  enable_deletion_protection = true

  tags = {
    Name = "${var.project_name}-eks-alb"

  }
}

resource "aws_lb_target_group" "http" {
  name        = "eks-http"
  target_type = "instance"
  port        = "30080"
  protocol    = "HTTP"
  vpc_id      = var.vpc_id

  health_check {
    path     = "/"
    port     = "30080"
    protocol = "HTTP"
    matcher  = "200,404"
  }

  tags = {
    Name = "${var.project_name}-eks-alb-http-target-grp"
  }
}

resource "aws_lb_target_group" "https" {
  name        = "eks-https"
  target_type = "instance"
  port        = "30443"
  protocol    = "HTTPS"
  vpc_id      = var.vpc_id

  health_check {
    path     = "/"
    port     = "30443"
    protocol = "HTTPS"
    matcher  = "200,404"
  }

  tags = {
    Name = "${var.project_name}-eks-alb-https-target-grp"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb_for_eks.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.http.arn
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.alb_for_eks.arn
  port              = "443"
  protocol          = "HTTPS"
  certificate_arn   = aws_acm_certificate.ecomm_certificate.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.https.arn
  }
}

resource "aws_autoscaling_attachment" "asg_alb_attachment_http" {
  autoscaling_group_name = var.eks_nodes_asg_name
  lb_target_group_arn    = aws_lb_target_group.http.arn
}

resource "aws_autoscaling_attachment" "asg_alb_attachment_https" {
  autoscaling_group_name = var.eks_nodes_asg_name
  lb_target_group_arn    = aws_lb_target_group.https.arn
}