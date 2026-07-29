# test_05_check.py
import json
import logging

from kubernetes.client.rest import ApiException

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_no_pods_with_app_label_with_library(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        pod_namespace = json_input["namespace"]

        try:
            pods = k8s_client.list_namespaced_pod(namespace=pod_namespace)
            for pod in pods.items:
                assert (
                    "app" not in pod.metadata.labels
                ), f"Found Pod '{pod.metadata.name}' with label 'app'"
            logging.info(
                "No Pods with the label 'app' found in namespace '%s'", pod_namespace
            )
        except ApiException as e:
            if e.status == 404:
                logging.info(
                    "No pods found in namespace '%s', skipping check.", pod_namespace
                )
            else:
                raise

    def test_002_verify_no_pods_with_app_label_with_kubectl(self, json_input):
        logging.debug("Starting test_002_verify_no_pods_with_app_label_with_kubectl")
        kube_config = build_kube_config_from_input(json_input)

        pod_namespace = json_input["namespace"]

        command = f"kubectl get pods -n {pod_namespace} -o json"
        logging.debug("Running command: %s", command)
        result = run_kubectl_command(kube_config, command)
        logging.debug("Command result: %s", result)

        json_output = result.strip()
        logging.debug("Command output: %s", json_output)
        logging.info(json_output)

        pods_data = json.loads(json_output)
        for pod in pods_data["items"]:
            assert (
                "app" not in pod["metadata"]["labels"]
            ), f"Found Pod '{pod['metadata']['name']}' with label 'app'"
        logging.info(
            "No Pods with the label 'app' found in namespace '%s'", pod_namespace
        )
