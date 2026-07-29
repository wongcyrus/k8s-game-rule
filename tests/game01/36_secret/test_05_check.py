import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_secret_client(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        secret_name = "mysecret"
        expected_password = json_input["value1"]

        logging.info("Using namespace: %s", namespace)
        logging.info(
            "Checking Secret '%s' in namespace '%s' using client",
            secret_name,
            namespace,
        )

        try:
            secret = k8s_client.read_namespaced_secret(
                name=secret_name, namespace=namespace
            )
        except Exception as e:
            logging.error("Failed to get Secret '%s': %s", secret_name, str(e))
            assert False, f"Failed to get Secret '{secret_name}': {str(e)}"

        actual_password = secret.data["password"]
        assert (
            actual_password == expected_password
        ), f"Expected password to be '{expected_password}', but got '{actual_password}'."
        logging.info("Secret '%s' has the correct password value.", secret_name)

    def test_002_check_secret_kubectl(self, json_input):
        logging.debug("Starting test_002_check_secret_kubectl")
        kube_config = build_kube_config_from_input(json_input)
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
