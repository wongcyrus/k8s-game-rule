import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command

class TestCheck:
    def test_001_check_limitrange_client(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        limitrange_name = "mem-limit-range"

        logging.info(f"Using namespace: {namespace}")
        logging.info(f"Checking LimitRange '{limitrange_name}' in namespace '{namespace}' using client")

        # 验证 LimitRange 是否成功创建
        try:
            limitrange = k8s_client.read_namespaced_limit_range(name=limitrange_name, namespace=namespace)
        except Exception as e:
            logging.error(f"Failed to get LimitRange '{limitrange_name}': {str(e)}")
            assert False, f"Failed to get LimitRange '{limitrange_name}': {str(e)}"

        # 验证 LimitRange 中的内存限制
        limits = limitrange.spec.limits[0]
        assert limits.max["memory"] == "500Mi", f"Expected max memory to be '500Mi', but got '{limits.max['memory']}'."
        assert limits.min["memory"] == "100Mi", f"Expected min memory to be '100Mi', but got '{limits.min['memory']}'."
        assert limits.type == "Pod", f"Expected type to be 'Pod', but got '{limits.type}'."
        logging.info(f"LimitRange '{limitrange_name}' has the correct memory limits.")

    def test_002_check_limitrange_kubectl(self, json_input):
        logging.debug("Starting test_002_check_limitrange_kubectl")
        kube_config = build_kube_config_from_input(json_input)
        namespace = json_input["namespace"]
        limitrange_name = "mem-limit-range"

        logging.info(f"Using namespace: {namespace}")
        logging.info(f"Checking LimitRange '{limitrange_name}' in namespace '{namespace}' using kubectl")

        # 使用 kubectl 获取 LimitRange
        command = f"kubectl get limitrange {limitrange_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)

        # 解析 kubectl 输出的 JSON 内容
        limitrange = json.loads(result)

        # 验证 LimitRange 的内容
        assert limitrange["apiVersion"] == "v1", "Incorrect apiVersion."
        assert limitrange["kind"] == "LimitRange", "Incorrect kind."
        assert limitrange["metadata"]["name"] == limitrange_name, "Incorrect metadata.name."

        # 验证 LimitRange 中的内存限制
        limits = limitrange["spec"]["limits"][0]
        assert limits["max"]["memory"] == "500Mi", f"Expected max memory to be '500Mi', but got '{limits['max']['memory']}'."
        assert limits["min"]["memory"] == "100Mi", f"Expected min memory to be '100Mi', but got '{limits['min']['memory']}'."
        assert limits["type"] == "Pod", f"Expected type to be 'Pod', but got '{limits['type']}'."
        logging.info(f"LimitRange '{limitrange_name}' has the correct memory limits.")
