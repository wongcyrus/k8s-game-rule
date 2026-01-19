# test_05_check.py
import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:
    def test_001_verify_new_annotation(self, json_input):
        logging.debug("Starting test_001_verify_new_annotation")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        pod_namespace = json_input["namespace"]

        pod_names = ["nginx1", "nginx2", "nginx3"]

        for pod_name in pod_names:
            command = f"kubectl get pod {pod_name} -n {pod_namespace} -o json"
            logging.debug("Running command: %s", command)
            result = run_kubectl_command(kube_config, command)
            logging.debug("Command result: %s", result)

            pod_data = json.loads(result)
            logging.debug(
                "Current annotations for %s: %s", pod_name, pod_data["metadata"].get("annotations", {})
            )

            if pod_data["metadata"]["labels"].get("app") == "v2":
                assert (
                    pod_data["metadata"].get("annotations", {}).get("owner") == "marketing"
                ), f"Pod '{pod_name}' does not have the annotation 'owner=marketing'"
                logging.info(
                    "Pod '%s' has the annotation 'owner=marketing'", pod_name
                )
