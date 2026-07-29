import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:

    def test_001_check_configmap_client(self, json_input):
        k8s_client = configure_k8s_client(json_input)

        # 获取 ConfigMap
        configmap_name = "special-configmap"
        namespace = json_input["namespace"]

        try:
            configmap = k8s_client.read_namespaced_config_map(
                name=configmap_name, namespace=namespace
            )
        except Exception as e:
            assert False, f"Failed to get ConfigMap '{configmap_name}': {str(e)}"

        # 验证 ConfigMap 的内容
        assert configmap.api_version == "v1", "Incorrect apiVersion."
        assert configmap.kind == "ConfigMap", "Incorrect kind."
        assert configmap.metadata.name == configmap_name, "Incorrect metadata.name."
        assert "special" in configmap.data, "Missing key 'special' in data."
        assert (
            configmap.data["special"] == json_input["value1"]
        ), "Incorrect value for 'special'."
        logging.info("ConfigMap '%s' has the correct content.", configmap_name)

    def test_002_check_configmap_kubectl(self, json_input):
        logging.debug("Starting test_002_check_configmap_kubectl")
        kube_config = build_kube_config_from_input(json_input)

        namespace = json_input["namespace"]
        configmap_name = "special-configmap"

        # 使用 kubectl 获取 ConfigMap
        command = f"kubectl get configmap {configmap_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)
        logging.debug("Command result: %s", result)

        if "Error from server" in result:
            assert False, f"Failed to get ConfigMap '{configmap_name}': {result}"

        # 解析 kubectl 输出的 JSON 内容
        configmap = json.loads(result)

        # 验证 ConfigMap 的内容
        assert configmap["apiVersion"] == "v1", "Incorrect apiVersion."
        assert configmap["kind"] == "ConfigMap", "Incorrect kind."
        assert (
            configmap["metadata"]["name"] == configmap_name
        ), "Incorrect metadata.name."
        assert "special" in configmap["data"], "Missing key 'special' in data."
        assert (
            configmap["data"]["special"] == json_input["value1"]
        ), "Incorrect value for 'special'."
        logging.info("ConfigMap '%s' has the correct content.", configmap_name)
