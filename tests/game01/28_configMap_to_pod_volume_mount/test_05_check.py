import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_configmap_and_pod(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        value1 = json_input["value1"]
        value2 = json_input["value2"]
        configmap_name = "cmvolume"
        pod_name = "nginx-pod"

        # 验证 ConfigMap
        try:
            logging.info(
                "Checking ConfigMap '%s' in namespace '%s'", configmap_name, namespace
            )
            configmap = k8s_client.read_namespaced_config_map(
                name=configmap_name, namespace=namespace
            )
        except Exception as e:
            logging.error("Failed to get ConfigMap '%s': %s", configmap_name, str(e))
            assert False, f"Failed to get ConfigMap '{configmap_name}': {str(e)}"

        assert configmap.data["var8"] == value1, "Incorrect value for 'var8'."
        assert configmap.data["var9"] == value2, "Incorrect value for 'var9'."
        logging.info(
            "ConfigMap '%s' has the correct values for 'var8' and 'var9'.",
            configmap_name,
        )

        # 验证 Pod
        try:
            logging.info("Checking Pod '%s' in namespace '%s'", pod_name, namespace)
            pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception as e:
            logging.error("Failed to get Pod '%s': %s", pod_name, str(e))
            assert False, f"Failed to get Pod '{pod_name}': {str(e)}"

        # 验证 Pod 中的 volume 和 mountPath
        volume_mounts = {
            v.name: v.mount_path for v in pod.spec.containers[0].volume_mounts
        }
        assert (
            volume_mounts["config-volume"] == "/etc/lala"
        ), "Incorrect mountPath for config-volume in Pod."
        logging.info("Pod '%s' has the correct volume mountPath '/etc/lala'.", pod_name)

    def test_002_check_pod_details(self, json_input):
        logging.debug("Starting test_002_check_pod_details")
        kube_config = build_kube_config_from_input(json_input)
        namespace = json_input["namespace"]
        pod_name = "nginx-pod"

        command = f"kubectl get pod {pod_name} -n {namespace} -o json"
        logging.debug("Running command: %s", command)
        result = run_kubectl_command(kube_config, command)
        logging.debug("Command result: %s", result)

        pod_output = result.strip()
        logging.debug("Command output: %s", pod_output)
        logging.info(pod_output)

        pod_data = json.loads(pod_output)

        # 验证卷和 ConfigMap 的挂载
        volumes = [
            v for v in pod_data["spec"]["volumes"] if v["name"] == "config-volume"
        ]
        assert len(volumes) == 1, "Volume 'config-volume' not found in Pod."
        assert (
            volumes[0]["configMap"]["name"] == "cmvolume"
        ), "ConfigMap 'cmvolume' not found in volume."

        logging.info(
            "Pod '%s' has the correct volume with ConfigMap 'cmvolume'.", pod_name
        )
