import logging
import time

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_pod_creation(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        pod_name = "busybox-pod"

        logging.info("Using namespace: %s", namespace)
        logging.info(
            "Checking if Pod '%s' is created in namespace '%s' using client",
            pod_name,
            namespace,
        )

        # 验证 Pod 是否成功创建
        try:
            pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=namespace)
            assert (
                pod is not None
            ), f"Pod '{pod_name}' not found in namespace '{namespace}'"
            logging.info("Pod '%s' found in namespace '%s'", pod_name, namespace)
        except Exception as e:
            logging.error("Failed to get Pod '%s': %s", pod_name, str(e))
            assert False, f"Failed to get Pod '{pod_name}': {str(e)}"

    def test_002_check_pod_logs(self, json_input):
        logging.debug("Starting test_002_check_pod_logs")
        kube_config = build_kube_config_from_input(json_input)
        namespace = json_input["namespace"]
        pod_name = "busybox-pod"

        logging.info("Using namespace: %s", namespace)
        logging.info(
            "Checking logs for Pod '%s' in namespace '%s' using kubectl",
            pod_name,
            namespace,
        )

        # 等待 Pod 完全启动
        time.sleep(7)

        # 使用 kubectl 获取 Pod 日志
        command = f"kubectl logs {pod_name} -n {namespace} --tail=10"
        result = run_kubectl_command(kube_config, command)

        # 检查日志输出
        logs = result
        logging.info("Logs for Pod '%s':\n%s", pod_name, logs)
        assert "0: " in logs, "Expected log output not found."
