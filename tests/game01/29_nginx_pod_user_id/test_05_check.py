import json
import logging
import time

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:

    def test_001_check_pod_kubectl(self, json_input):
        logging.debug("Starting test_002_check_pod_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        pod_name = "nginx-pod"

        # 等待 Pod 创建和启动
        for _ in range(10):  # 尝试 10 次，每次间隔 5 秒
            command = f"kubectl get pod {pod_name} -n {namespace} -o json"
            result = run_kubectl_command(kube_config, command)
            pod_data = json.loads(result)
            if pod_data["status"]["phase"] == "Running":
                logging.info("Pod '%s' is in Running state.", pod_name)
                break  # Pod 处于 Running 状态，可以退出
            time.sleep(5)  # 等待 5 秒后再次检查
        
        # 使用 kubectl 获取 Pod
        command = f"kubectl get pod {pod_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)

        # 解析 kubectl 输出的 JSON 内容
        pod = json.loads(result)

        # 验证 Pod 的内容
        assert pod["apiVersion"] == "v1", "Incorrect apiVersion."
        assert pod["kind"] == "Pod", "Incorrect kind."
        assert pod["metadata"]["name"] == "nginx-pod", "Incorrect metadata.name."

        # 验证 Pod 中的 runAsUser
        run_as_user = int(pod["spec"]["securityContext"]["runAsUser"])
        expected_user = int(json_input["value1"])  # 确保 value1 是整数类型
        assert run_as_user == expected_user, f"Expected runAsUser to be '{expected_user}', but got '{run_as_user}'."
        logging.info("Pod '%s' has the correct runAsUser '%s'.", pod_name, expected_user)

        # 验证 Pod 中的容器镜像
        container_image = pod["spec"]["containers"][0]["image"]
        assert container_image == "nginx", f"Expected container image to be 'nginx', but got '{container_image}'."
        logging.info("Pod '%s' has the correct container image 'nginx'.", pod_name)
