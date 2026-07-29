import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:

    def test_001_pod_exists_with_library(self, json_input):
        logging.debug(json_input)
        k8s_client = configure_k8s_client(json_input)
        pod_name = "nginx"
        pod_namespace = "default"
        pods = k8s_client.list_namespaced_pod(namespace=pod_namespace)
        pod_names = [pod.metadata.name for pod in pods.items]
        assert (
            pod_name in pod_names
        ), f"Pod '{pod_name}' does not exist in namespace '{pod_namespace}'"

    def test_002_pod_exists_with_kubectl(self, json_input):
        kube_config = build_kube_config_from_input(json_input)
        command = "kubectl get pods -n default"
        result = run_kubectl_command(kube_config, command)
        logging.info(result)
        pod_name = "nginx"
        assert (
            pod_name in result
        ), f"Pod '{pod_name}' does not exist in namespace 'default'"
