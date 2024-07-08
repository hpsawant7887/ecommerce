resource "aws_eks_cluster" "eks_cluster" {
  name     = "${var.project_name}-eks-cluster"

  # The Amazon Resource Name (ARN) of the IAM role that provides permissions for the Kubernetes control plane to make calls to AWS API operations

  role_arn = aws_iam_role.eks_cluster_iam_role.arn
  # Desired Kubernetes master version
  version = "1.30"
  vpc_config {
    security_group_ids      = [var.eks_cluster_sg_id, var.eks_worker_sg_id]
    endpoint_private_access = false
    endpoint_public_access  = true
    subnet_ids              = var.subnet_id_list  # this is of type list
  }
}


resource "aws_launch_template" "eks_nodes_launch_template" {
  name = "eks_nodes_launch_template"

  block_device_mappings {
    device_name = "/dev/sda"

    ebs {
      volume_size = 20
    }
  }

  image_id = "ami-0a9cf50724f161558"

  vpc_security_group_ids = [var.eks_worker_sg_id]

}

resource "aws_eks_node_group" "node_group" {
  # Name of the EKS Cluster
  cluster_name = aws_eks_cluster.eks_cluster.id

  # Name of the EKS Node Group.
  node_group_name = "${aws_eks_cluster.eks_cluster.id}-node_group"

  # Amazon Resource Name (ARN) of the IAM Role that provides permissions for the EKS Node Group.
  node_role_arn = aws_iam_role.node_group_role.arn

  # Identifiers of EC2 Subnets to associate with the EKS Node Group. 
  # These subnets must have the following resource tag: kubernetes.io/cluster/EKS_CLUSTER_NAME 

  subnet_ids = var.subnet_id_list

  # Configuration block
  scaling_config {
    # Required number of worker nodes
    desired_size = 2

    # Maximum number of worker nodes
    max_size = 2

    # Minimum number of worker nodes
    min_size = 2
  }

  # # Type of Amazon Machine Image (AMI) associated with the EKS Node Group
 
  ami_type = "AL2_ARM_64"

  # Type of capacity associated with the EKS Node Group

  capacity_type = "ON_DEMAND"

  # Disk size in GB for worker nodes
  # disk_size = 20

  # Force version update if existing pods are unable to be drained due to a pod disruption budget issue
  force_update_version = false

  # Instance type associated with the EKS Node Group
  instance_types = ["t4g.xlarge"]

  launch_template { 
    id = aws_launch_template.eks_nodes_launch_template.id 
    version = aws_launch_template.eks_nodes_launch_template.default_version   
  }

  labels = {
    role = "${aws_eks_cluster.eks_cluster.id}-Node-group-role",
    name = "${aws_eks_cluster.eks_cluster.id}-node_group"
  }

  # Kubernetes version
  version = "1.30"
}

data "aws_eks_addon_version" "addon_version_vpc_cni" {
  addon_name         = "vpc-cni"
  kubernetes_version = aws_eks_cluster.eks_cluster.version
  most_recent        = true
}

data "aws_eks_addon_version" "addon_version_kube_proxy" {
  addon_name         = "kube-proxy"
  kubernetes_version = aws_eks_cluster.eks_cluster.version
  most_recent        = true
}

data "aws_eks_addon_version" "addon_version_coredns" {
  addon_name         = "coredns"
  kubernetes_version = aws_eks_cluster.eks_cluster.version
  most_recent        = true
}


data "aws_eks_addon_version" "addon_version_csi" {
  addon_name         = "aws-ebs-csi-driver"
  kubernetes_version = aws_eks_cluster.eks_cluster.version
  most_recent        = true
}

resource "aws_eks_addon" "vpc_cni_addon" {
  cluster_name = aws_eks_cluster.eks_cluster.name
  addon_name   = "vpc-cni"

  addon_version  = data.aws_eks_addon_version.addon_version_vpc_cni.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  service_account_role_arn    = null

  depends_on = [
    aws_eks_node_group.node_group
  ]

}

resource "aws_eks_addon" "csi_addon" {
  cluster_name = aws_eks_cluster.eks_cluster.name
  addon_name   = "aws-ebs-csi-driver"

  addon_version               = data.aws_eks_addon_version.addon_version_csi.version
  configuration_values        = null
  preserve                    = true
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  service_account_role_arn    = null

  depends_on = [
    aws_eks_node_group.node_group
  ]

}


resource "aws_eks_addon" "kube_proxy_addon" {
  cluster_name  = aws_eks_cluster.eks_cluster.id
  addon_name    = "kube-proxy"

  addon_version = data.aws_eks_addon_version.addon_version_kube_proxy.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  service_account_role_arn    = null

  depends_on = [
    aws_eks_node_group.node_group
  ]
}

resource "aws_eks_addon" "coredns_addon" {
  cluster_name  = aws_eks_cluster.eks_cluster.name
  addon_name    = "coredns"

  addon_version = data.aws_eks_addon_version.addon_version_coredns.version
  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
  service_account_role_arn    = null

  depends_on = [
    aws_eks_node_group.node_group
  ]

}




