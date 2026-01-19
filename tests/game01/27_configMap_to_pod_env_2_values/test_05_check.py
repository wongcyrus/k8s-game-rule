import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command


class TestCheck:
    def test_001_check_configmap_and_pod(self, json_input):
        logging.debug("Starting test_001_check_configmap_and_pod")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        value1 = json_input["value1"]
        value2 = json_input["value2"]
        configmap_name = json_input["configmap_name"]

        # Verify ConfigMap
        command = f"kubectl get configmap {configmap_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)
        configmap_data = json.loads(result)
        
        assert configmap_data["data"]["var6"] == value1, "Incorrect value for 'var6'."
        assert configmap_data["data"]["var7"] == value2, "Incorrect value for 'var7'."
        logging.info(
            "ConfigMap '%s' has the correct values for 'var6' and 'var7'.",
            configmap_name,
        )

    def test_002_check_pod_env_var_with_kubectl(self, json_input):
        logging.debug("Starting test_002_check_pod_env_var_with_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        configmap_name = json_input["configmap_name"]
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
            env_vars["var6"]["name"] == configmap_name
        ), "Incorrect ConfigMap name for 'var6' in environment variable."
        assert (
            env_vars["var6"]["key"] == "var6"
        ), "Incorrect key for 'var6' in environment variable."
        assert (
            env_vars["var7"]["name"] == configmap_name
        ), "Incorrect ConfigMap name for 'var7' in environment variable."
        assert (
            env_vars["var7"]["key"] == "var7"
        ), "Incorrect key for 'var7' in environment variable."
        logging.info(
            "Pod '%s' has the correct environment variables from ConfigMap.", pod_name
        )
