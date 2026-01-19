import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:
    def test_001_pod_label_with_kubectl(self, json_input):
        logging.debug("Starting test_001_pod_label_with_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        command = f"kubectl get pod nginx2 -n {json_input['namespace']} -o json"
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
                pod_data["metadata"]["labels"].get("app") == "v2"
            ), "Pod label 'app' is not 'v2'"
            assert pod_data["metadata"]["name"] == "nginx2", "Pod name is not 'nginx2'"
