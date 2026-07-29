import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_pod_client(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        pod_name = "nginx-pod"

        # 验证 Pod
        try:
            logging.info(
                "Checking Pod '%s' in namespace '%s' using client", pod_name, namespace
            )
            pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception as e:
            logging.error("Failed to get Pod '%s': %s", pod_name, str(e))
            assert False, f"Failed to get Pod '{pod_name}': {str(e)}"

        # 验证 Pod 中的内存请求
        resources = pod.spec.containers[0].resources
        memory_request = (
            resources.requests["memory"] if resources and resources.requests else None
        )
        assert (
            memory_request == "250Mi"
        ), f"Expected memory request to be '250Mi', but got '{memory_request}'."
        logging.info("Pod '%s' has the correct memory request: '250Mi'.", pod_name)

    def test_002_check_pod_kubectl(self, json_input):
        logging.debug("Starting test_002_check_pod_kubectl")
        kube_config = build_kube_config_from_input(json_input)
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
        assert pod["metadata"]["name"] == pod_name, "Incorrect metadata.name."

        # 验证 Pod 中的内存请求
        resources = pod["spec"]["containers"][0]["resources"]
        memory_request = (
            resources["requests"]["memory"]
            if resources and "requests" in resources
            else None
        )
        assert (
            memory_request == "250Mi"
        ), f"Expected memory request to be '250Mi', but got '{memory_request}'."
        logging.info("Pod '%s' has the correct memory request: '250Mi'.", pod_name)
