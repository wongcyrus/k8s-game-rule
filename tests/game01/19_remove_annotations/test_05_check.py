import json
import logging
from subprocess import CalledProcessError

from kubernetes.client.rest import ApiException

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_ensure_no_annotations_via_library(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        pod_list = ["nginx1", "nginx2", "nginx3"]

        for pod_name in pod_list:
            try:
                pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=namespace)
                # annotations = pod.metadata.annotations or {}
                annotations = (
                    pod.metadata.annotations
                    if pod.metadata.annotations is not None
                    else {}
                )
                assert (
                    "description" not in annotations
                ), f"Pod '{pod_name}' has leftover annotations: {annotations}"
                assert (
                    "description" not in annotations
                ), f"Pod '{pod_name}' has a 'description' annotation: {annotations['description']}"
                logging.info("Confirmed pod '%s' has no annotations.", pod_name)
            except ApiException as exc:
                if exc.status == 404:
                    logging.info("Pod '%s' not found; skipping validation.", pod_name)
                else:
                    raise

    def test_002_ensure_no_annotations_via_kubectl(self, json_input):
        logging.debug("Starting test_002_ensure_no_annotations_via_kubectl")
        kube_cfg = build_kube_config_from_input(json_input)

        namespace = json_input["namespace"]
        pod_list = ["nginx1", "nginx2", "nginx3"]

        for pod_name in pod_list:
            cmd = f"kubectl get pod {pod_name} -n {namespace} -o json"
            logging.debug("Executing command: %s", cmd)
            output = run_kubectl_command(kube_cfg, cmd)
            logging.debug("Command output: %s", output.strip())

            pod_data = json.loads(output)
            annotations = pod_data["metadata"].get("annotations", {})
            assert (
                "description" not in annotations
            ), f"Pod '{pod_name}' has leftover annotations: {annotations}"
            logging.info("Confirmed pod '%s' has no annotations.", pod_name)
