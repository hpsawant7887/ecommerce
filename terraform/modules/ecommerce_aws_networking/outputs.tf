output "vpc_id" {
  value = aws_vpc.vpc.id
}

output "subnet_id_list" {
  value = [ for subnet in aws_subnet.private_subnet: subnet.id ]
}

output "eks_cluster_sg" {
  value = aws_security_group.eks_cluster_sg.id
}

output "eks_worker_nodes_sg" {
  value = aws_security_group.eks_nodes_sg.id
}

output "public_subnet_id_list" {
  value = [for subnet in aws_subnet.public_subnet: subnet.id]
}

output "private_subnet_route_table_id_list" {
  value = [for rt in aws_route_table.private_subnet_route_table: rt.id ]
}

output "public_subnet_route_table_id_list" {
  value = [aws_route_table.pub_rt.id]
}


