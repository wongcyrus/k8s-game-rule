# test_05_check.py
import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_pods_annotation_with_library(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        pod_namespace = json_input["namespace"]

        pod_names = ["nginx1", "nginx2", "nginx3"]

        for pod_name in pod_names:
            pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=pod_namespace)
            annotations = (
                pod.metadata.annotations if pod.metadata.annotations is not None else {}
            )
            assert (
                annotations.get("description") == "my description"
            ), f"Pod '{pod_name}' does not have the annotation 'description=my description'"
            logging.info(
                "Pod '%s' has the annotation 'description=my description'", pod_name
            )

    def test_002_verify_pods_annotation_with_kubectl(self, json_input):
        logging.debug("Starting test_002_verify_pods_annotation_with_kubectl")
        kube_config = build_kube_config_from_input(json_input)

        pod_namespace = json_input["namespace"]
        pod_names = ["nginx1", "nginx2", "nginx3"]

        for pod_name in pod_names:
            command = f"kubectl get pod {pod_name} -n {pod_namespace} -o json"
            logging.debug("Running command: %s", command)
            result = run_kubectl_command(kube_config, command)
            logging.debug("Command result: %s", result)

            json_output = result.strip()
            logging.debug("Command output: %s", json_output)
            logging.info(json_output)

            pod_data = json.loads(json_output)
            annotations = pod_data["metadata"].get("annotations", {})
            assert (
                annotations.get("description") == "my description"
            ), f"Pod '{pod_name}' does not have the annotation 'description=my description'"
            logging.info(
                "Pod '%s' has the annotation 'description=my description'", pod_name
            )
