import json
import logging

from kubernetes.client.rest import ApiException

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_label_tier_web_added_with_library(self, json_input):
        client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]

        try:
            pods = client.list_namespaced_pod(namespace=namespace)
            for pod in pods.items:
                labels = pod.metadata.labels or {}
                if labels.get("app") in ["v1", "v2"]:
                    assert labels.get("tier") == "web", (
                        f"Pod '{pod.metadata.name}' with 'app={labels.get('app')}' "
                        "is missing the 'tier=web' label"
                    )
                    logging.info(
                        "Pod '%s' with 'app=%s' has 'tier=web'",
                        pod.metadata.name,
                        labels.get("app"),
                    )
        except ApiException as exc:
            if exc.status == 404:
                logging.info(
                    "No pods discovered in namespace '%s'. Skipping.", namespace
                )
            else:
                raise

    def test_002_verify_label_tier_web_added_with_kubectl(self, json_input):
        logging.debug("Initiating test_002_verify_label_tier_web_added_with_kubectl")
        kube_cfg = build_kube_config_from_input(json_input)
        namespace = json_input["namespace"]

        cmd = f"kubectl get pods -n {namespace} -o json"
        logging.debug("Executing command: %s", cmd)
        outcome = run_kubectl_command(kube_cfg, cmd)
        logging.debug("Command execution result: %s", outcome)

        output_str = outcome.strip()
        logging.debug("Output processed: %s", output_str)
        logging.info(output_str)

        pods_info = json.loads(output_str)
        for pod in pods_info["items"]:
            labels = pod["metadata"].get("labels", {})
            if labels.get("app") in ["v1", "v2"]:
                assert labels.get("tier") == "web", (
                    f"Pod '{pod['metadata']['name']}' with 'app={labels.get('app')}' "
                    "does not include the 'tier=web' label"
                )
                logging.info(
                    "Pod '%s' with 'app=%s' has 'tier=web'",
                    pod["metadata"]["name"],
                    labels.get("app"),
                )
