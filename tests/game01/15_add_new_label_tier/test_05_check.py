import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:
    def test_001_verify_label_tier_web_added_with_kubectl(self, json_input):
        logging.debug("Initiating test_002_verify_label_tier_web_added_with_kubectl")
        kube_cfg = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
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
