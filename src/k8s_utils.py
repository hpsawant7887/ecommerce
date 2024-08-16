from kubernetes import client, config

def get_service_endpoint(service_name, namespace):
    config.load_incluster_config()

    v1 = client.CoreV1Api()

    service = v1.read_namespaced_service(service_name, namespace)

    if service.spec.type == "ClusterIP":
        cluster_ip = service.spec.cluster_ip
        port = service.spec.ports[0].port  # Assuming you want the first port
        endpoint = f"{cluster_ip}:{port}"

    return endpoint