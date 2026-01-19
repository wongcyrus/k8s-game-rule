import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:
    def test_001_pod_attributes_with_kubectl(self, json_input):
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        command = "kubectl get pod nginx -n default -o json"
        result = run_kubectl_command(kube_config, command)

        if "error" in result.lower():
            logging.error("Command failed with error: %s", result)
        else:
            json_output = result.strip()
            logging.info(json_output)

            pod_data = json.loads(json_output)

            assert (
                pod_data["spec"]["containers"][0]["image"] == "nginx:1.24.0"
            ), "Pod image version is not nginx:1.24.0"
            assert (
                pod_data["spec"]["containers"][0]["ports"][0]["containerPort"] == 80
            ), "Pod containerPort is not 80"
            assert (
                pod_data["metadata"]["namespace"] == "default"
            ), "Pod namespace is not default"
            assert pod_data["metadata"]["name"] == "nginx", "Pod name is not nginx"
