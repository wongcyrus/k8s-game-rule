import base64
import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_secret_client(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        secret_name = "ilovek8s"

        logging.info("Using namespace: %s", namespace)
        logging.info(
            "Checking Secret '%s' in namespace '%s' using client",
            secret_name,
            namespace,
        )

        # 验证 Secret
        try:
            secret = k8s_client.read_namespaced_secret(
                name=secret_name, namespace=namespace
            )
        except Exception as e:
            logging.error("Failed to get Secret '%s': %s", secret_name, str(e))
            assert False, f"Failed to get Secret '{secret_name}': {str(e)}"

        # 验证 Secret 中的 API_KEY 值
        api_key_value = base64.b64decode(secret.data["API_KEY"]).decode()
        assert (
            api_key_value == "ilovek8s"
        ), f"Expected API_KEY to be 'ilovek8s', but got '{api_key_value}'."
        logging.info("Secret '%s' has the correct API_KEY value.", secret_name)

    def test_002_check_secret_kubectl(self, json_input):
        logging.debug("Starting test_002_check_secret_kubectl")
        kube_config = build_kube_config_from_input(json_input)
        namespace = json_input["namespace"]
        secret_name = "ilovek8s"

        logging.info("Using namespace: %s", namespace)
        logging.info(
            "Checking Secret '%s' in namespace '%s' using kubectl",
            secret_name,
            namespace,
        )

        # 使用 kubectl 获取 Secret
        command = f"kubectl get secret {secret_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)

        # 解析 kubectl 输出的 JSON 内容
        secret = json.loads(result)

        # 验证 Secret 的内容
        assert secret["apiVersion"] == "v1", "Incorrect apiVersion."
        assert secret["kind"] == "Secret", "Incorrect kind."
        assert secret["metadata"]["name"] == secret_name, "Incorrect metadata.name."

        # 验证 Secret 中的 API_KEY 值
        api_key_value = base64.b64decode(secret["data"]["API_KEY"]).decode()
        assert (
            api_key_value == "ilovek8s"
        ), f"Expected API_KEY to be 'ilovek8s', but got '{api_key_value}'."
        logging.info("Secret '%s' has the correct API_KEY value.", secret_name)
