import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:

    def test_001_check_secret_kubectl(self, json_input):
        logging.debug("Starting test_002_check_secret_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        secret_name = "mysecret"
        expected_password = json_input["value1"]

        logging.info("Using namespace: %s", namespace)
        logging.info(
            "Checking Secret '%s' in namespace '%s' using kubectl",
            secret_name,
            namespace,
        )

        command = f"kubectl get secret {secret_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)
        secret = json.loads(result)

        assert secret["apiVersion"] == "v1", "Incorrect apiVersion."
        assert secret["kind"] == "Secret", "Incorrect kind."
        assert secret["metadata"]["name"] == secret_name, "Incorrect metadata.name."

        actual_password = secret["data"]["password"]
        assert (
            actual_password == expected_password
        ), f"Expected password to be '{expected_password}', but got '{actual_password}'."
        logging.info("Secret '%s' has the correct password value.", secret_name)
