import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:
    def test_001_ensure_no_annotations_via_kubectl(self, json_input):
        logging.debug("Starting test_002_ensure_no_annotations_via_kubectl")
        kube_cfg = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )

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
