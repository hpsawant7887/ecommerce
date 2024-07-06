# https://github.com/hashicorp/terraform-provider-aws/issues/37670

# https://github.com/hashicorp/terraform-provider-aws/pull/37885

resource "aws_route53domains_registered_domain" "ecomm_domain" {
  domain_name = var.root_domain_name
}

# resource "aws_route53_zone" "ecomm_r53_zone" {
#   name = var.root_domain_name
# }

data "aws_route53_zone" "ecomm_r53_zone" {
  name         = var.root_domain_name
  depends_on   = [
    aws_route53domains_registered_domain.ecomm_domain
  ]
}

resource "aws_acm_certificate" "ecomm_certificate" {
  domain_name       = var.root_domain_name
  validation_method = "DNS"
  
  subject_alternative_names = [
    "*.${var.root_domain_name}"
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "ecomm_cert_dns" {
  allow_overwrite = true
  name =  tolist(aws_acm_certificate.ecomm_certificate.domain_validation_options)[0].resource_record_name
  records = [tolist(aws_acm_certificate.ecomm_certificate.domain_validation_options)[0].resource_record_value]
  type = tolist(aws_acm_certificate.ecomm_certificate.domain_validation_options)[0].resource_record_type
  zone_id = data.aws_route53_zone.ecomm_r53_zone.zone_id
  ttl = 60
}

resource "aws_acm_certificate_validation" "ecomm_cert_validate" {
  certificate_arn = aws_acm_certificate.ecomm_certificate.arn
  validation_record_fqdns = [aws_route53_record.ecomm_cert_dns.fqdn]
}

resource "aws_route53_record" "ecomm_a_record" {
  zone_id = data.aws_route53_zone.ecomm_r53_zone.zone_id
  name    = "www.${var.root_domain_name}"
  type    = "A"
  alias {
    name                   = aws_lb.alb_for_eks.dns_name
    zone_id                = aws_lb.alb_for_eks.zone_id
    evaluate_target_health = false
  }
}