import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:

    def test_001_check_configmap_kubectl(self, json_input):
        logging.debug("Starting test_002_check_configmap_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )

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
