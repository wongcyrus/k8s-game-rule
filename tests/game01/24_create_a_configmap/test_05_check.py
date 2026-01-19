# test_05_check_configmap.py
import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheckConfigMap:

    def test_001_check_configmap_kubectl(self, json_input):
        logging.debug("Starting test_002_check_configmap_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )

        # 使用kubectl获取ConfigMap
        command = f"kubectl get configmap config -n {json_input['namespace']} -o json"
        result = run_kubectl_command(kube_config, command)

        # 解析kubectl输出的JSON内容
        configmap = json.loads(result)

        # 验证ConfigMap的内容
        assert configmap["apiVersion"] == "v1", "Incorrect apiVersion."
        assert configmap["kind"] == "ConfigMap", "Incorrect kind."
        assert configmap["metadata"]["name"] == "config", "Incorrect metadata.name."
        assert "foo" in configmap["data"], "Missing key 'foo' in data."
        assert (
            configmap["data"]["foo"] == json_input["value1"]
        ), "Incorrect value for 'foo'."
        assert "foo2" in configmap["data"], "Missing key 'foo2' in data."
        assert (
            configmap["data"]["foo2"] == json_input["value2"]
        ), "Incorrect value for 'foo2'."
        logging.info("ConfigMap 'config' has the correct content.")
