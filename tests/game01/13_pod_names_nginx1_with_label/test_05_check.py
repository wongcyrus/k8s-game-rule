import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_pod_label_with_library(self, json_input):
        logging.debug(json_input)
        k8s_client = configure_k8s_client(json_input)
        pod_name = "nginx1"
        pod_namespace = "default"
        pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=pod_namespace)

        assert pod.metadata.labels.get("app") == "v1", "Pod label 'app' is not 'v1'"
        assert pod.metadata.name == "nginx1", "Pod name is not 'nginx1'"

    def test_002_pod_label_with_kubectl(self, json_input):
        logging.debug("Starting test_002_pod_label_with_kubectl")
        kube_config = build_kube_config_from_input(json_input)
        command = "kubectl get pod nginx1 -n default -o json"
        logging.debug("Running command: %s", command)
        result = run_kubectl_command(kube_config, command)
        logging.debug("Command result: %s", result)

        if "error" in result.lower():
            logging.error("Command failed with error: %s", result)
        else:
            json_output = result.strip()
            logging.debug("Command output: %s", json_output)
            logging.info(json_output)

            pod_data = json.loads(json_output)

            assert (
                pod_data["metadata"]["labels"].get("app") == "v1"
            ), "Pod label 'app' is not 'v1'"
            assert pod_data["metadata"]["name"] == "nginx1", "Pod name is not 'nginx1'"
