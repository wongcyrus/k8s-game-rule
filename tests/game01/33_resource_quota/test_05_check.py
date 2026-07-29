import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_resourcequota_client(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        resourcequota_name = "resource-quota"

        # 验证 ResourceQuota
        try:
            logging.info(
                "Checking ResourceQuota '%s' in namespace '%s' using client",
                resourcequota_name,
                namespace,
            )
            resourcequota = k8s_client.read_namespaced_resource_quota(
                name=resourcequota_name, namespace=namespace
            )
        except Exception as e:
            logging.error(
                "Failed to get ResourceQuota '%s': %s", resourcequota_name, str(e)
            )
            assert (
                False
            ), f"Failed to get ResourceQuota '{resourcequota_name}': {str(e)}"

        # 验证 ResourceQuota 中的硬性限制
        hard = resourcequota.spec.hard
        assert (
            hard["requests.cpu"] == "1"
        ), f"Expected requests.cpu to be '1', but got '{hard['requests.cpu']}'."
        assert (
            hard["requests.memory"] == "1Gi"
        ), f"Expected requests.memory to be '1Gi', but got '{hard['requests.memory']}'."
        assert (
            hard["limits.cpu"] == "2"
        ), f"Expected limits.cpu to be '2', but got '{hard['limits.cpu']}'."
        assert (
            hard["limits.memory"] == "2Gi"
        ), f"Expected limits.memory to be '2Gi', but got '{hard['limits.memory']}'."
        logging.info(
            "ResourceQuota '%s' has the correct hard limits.", resourcequota_name
        )

    def test_002_check_resourcequota_kubectl(self, json_input):
        logging.debug("Starting test_002_check_resourcequota_kubectl")
        kube_config = build_kube_config_from_input(json_input)
        namespace = json_input["namespace"]
        resourcequota_name = "resource-quota"

        # 使用 kubectl 获取 ResourceQuota
        command = (
            f"kubectl get resourcequota {resourcequota_name} -n {namespace} -o json"
        )
        result = run_kubectl_command(kube_config, command)

        # 解析 kubectl 输出的 JSON 内容
        resourcequota = json.loads(result)

        # 验证 ResourceQuota 的内容
        assert resourcequota["apiVersion"] == "v1", "Incorrect apiVersion."
        assert resourcequota["kind"] == "ResourceQuota", "Incorrect kind."
        assert (
            resourcequota["metadata"]["name"] == resourcequota_name
        ), "Incorrect metadata.name."

        # 验证 ResourceQuota 中的硬性限制
        hard = resourcequota["spec"]["hard"]
        assert (
            hard["requests.cpu"] == "1"
        ), f"Expected requests.cpu to be '1', but got '{hard['requests.cpu']}'."
        assert (
            hard["requests.memory"] == "1Gi"
        ), f"Expected requests.memory to be '1Gi', but got '{hard['requests.memory']}'."
        assert (
            hard["limits.cpu"] == "2"
        ), f"Expected limits.cpu to be '2', but got '{hard['limits.cpu']}'."
        assert (
            hard["limits.memory"] == "2Gi"
        ), f"Expected limits.memory to be '2Gi', but got '{hard['limits.memory']}'."
        logging.info(
            "ResourceQuota '%s' has the correct hard limits.", resourcequota_name
        )
