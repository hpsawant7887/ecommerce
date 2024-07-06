output "eks_nodes_asg_name" {
    value = lookup(lookup(lookup(aws_eks_node_group.node_group, "resources")[0], "autoscaling_groups")[0], "name")
}