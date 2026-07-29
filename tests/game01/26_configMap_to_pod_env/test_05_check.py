import json
import logging

from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCheck:
    def test_001_check_configmap_and_pod(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        namespace = json_input["namespace"]
        value1 = json_input["value1"]
        configmap_name = "options"
        pod_name = "nginx"

        # 验证 ConfigMap
        try:
            configmap = k8s_client.read_namespaced_config_map(
                name=configmap_name, namespace=namespace
            )
        except Exception as e:
            assert False, f"Failed to get ConfigMap '{configmap_name}': {str(e)}"

        assert configmap.data["var5"] == value1, "Incorrect value for 'var5'."
        logging.info(
            "ConfigMap '%s' has the correct value for '%s'.", configmap_name, value1
        )

        # 验证 Pod
        try:
            pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception as e:
            assert False, f"Failed to get Pod '{pod_name}': {str(e)}"

        env_vars = {
            env.name: env.value_from.config_map_key_ref
            for env in pod.spec.containers[0].env
        }
        assert (
            env_vars["option"].name == configmap_name
        ), "Incorrect ConfigMap name in environment variable."
        assert (
            env_vars["option"].key == "var5"
        ), "Incorrect key in environment variable."
        logging.info(
            "Pod '%s' has the correct environment variable from ConfigMap.", pod_name
        )

    def test_002_check_pod_env_var_with_kubectl(self, json_input):
        logging.debug("Starting test_002_check_pod_env_var_with_kubectl")
        kube_config = build_kube_config_from_input(json_input)
        namespace = json_input["namespace"]
        pod_name = "nginx"

        command = f"kubectl get pod {pod_name} -n {namespace} -o json"
        logging.debug("Running command: %s", command)
        result = run_kubectl_command(kube_config, command)
        logging.debug("Command result: %s", result)

        json_output = result.strip()
        logging.debug("Command output: %s", json_output)
        logging.info(json_output)

        pod_data = json.loads(json_output)
        env_vars = {
            env["name"]: env["valueFrom"]["configMapKeyRef"]
            for env in pod_data["spec"]["containers"][0]["env"]
        }
        assert (
            env_vars["option"]["name"] == "options"
        ), "Incorrect ConfigMap name in environment variable."
        assert (
            env_vars["option"]["key"] == "var5"
        ), "Incorrect key in environment variable."
        logging.info(
            "Pod '%s' has the correct environment variable from ConfigMap.", pod_name
        )
