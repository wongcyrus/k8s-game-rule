import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:

    def test_001_check_pod_kubectl(self, json_input):
        logging.debug("Starting test_002_check_pod_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        pod_name = "nginx-pod"

        # 使用 kubectl 获取 Pod
        command = f"kubectl get pod {pod_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)

        # 解析 kubectl 输出的 JSON 内容
        pod = json.loads(result)

        # 验证 Pod 的内容
        assert pod["apiVersion"] == "v1", "Incorrect apiVersion."
        assert pod["kind"] == "Pod", "Incorrect kind."
        assert pod["metadata"]["name"] == "nginx-pod", "Incorrect metadata.name."

        # 验证 Pod 中的 capabilities
        capabilities = pod["spec"]["containers"][0]["securityContext"]["capabilities"]["add"]
        expected_capabilities = ["NET_ADMIN", "SYS_TIME"]
        assert all(cap in capabilities for cap in expected_capabilities), f"Expected capabilities {expected_capabilities}, but got {capabilities}."
        logging.info("Pod '%s' has the correct capabilities '%s'.", pod_name, expected_capabilities)
