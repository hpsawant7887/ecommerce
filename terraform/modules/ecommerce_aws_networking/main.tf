# Create VPC

resource "aws_vpc" "vpc" {
  cidr_block = var.cidr_block
  instance_tenancy = "default"
  enable_dns_hostnames = true
  enable_dns_support   = true
  # enable_classiclink   = false
  # enable_classiclink_dns_support = false
  assign_generated_ipv6_cidr_block = false

 tags = {
   Name = "${var.project_name}-vpc"
 }
}

# use data source to get avalablility zones in the region
data "aws_availability_zones" "availability_zones" {}

# Public Subnet
resource "aws_subnet" "public_subnet" {
  vpc_id                    = aws_vpc.vpc.id
  cidr_block                = var.public_subnet_cidr
  map_public_ip_on_launch   = true
  availability_zone         = data.aws_availability_zones.availability_zones.names[0]

  tags = {
    Name                        = "public_subnet"
    "kubernetes.io/cluster/${var.project_name}-eks-cluster" = "shared"
    "kubernetes.io/role/elb" = 1
  }
}

# IGW
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Route Table
resource "aws_route_table" "pub_rt" {
  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "${var.project_name}-pub_rt"
  }
}

# Public Route Table Association
resource "aws_route_table_association" "pub_rt_a" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.pub_rt.id
}

# Elastic IP for NAT GW
resource "aws_eip" "eip_nat_gw" {
  domain =  "vpc"

  tags = {
    Name = "nat_gw_eip"
  }
}

# NAT GW
resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.eip_nat_gw.id
  subnet_id     = aws_subnet.public_subnet.id

  tags = {
    Name = "nat_gw1"
  }

  # To ensure proper ordering, it is recommended to add an explicit dependency
  # on the Internet Gateway for the VPC.
  depends_on = [aws_internet_gateway.igw]
}


# Private Subnet 1
resource "aws_subnet" "private_subnet" {
  for_each = var.private_subnet_cidrs

  vpc_id             = aws_vpc.vpc.id
  cidr_block         = each.key
  availability_zone  = each.value
  map_public_ip_on_launch = false
  
  tags = {
    Name                        = "pri-sub-${each.value}"
    "kubernetes.io/cluster/${var.project_name}-eks-cluster" = "shared"
  }
}

# Private Route table
resource "aws_route_table" "private_subnet_route_table" {
  for_each = var.private_subnet_cidrs

  vpc_id = aws_vpc.vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_gw.id
  }

  tags = {
    Name = "pri_rt_a"
  }
}

# Route table association
resource "aws_route_table_association" "private_subnet_route_table_association" {
  for_each = var.private_subnet_cidrs

  subnet_id      = aws_subnet.private_subnet[each.key].id
  route_table_id = aws_route_table.private_subnet_route_table[each.key].id
}


