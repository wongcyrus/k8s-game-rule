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
        configmap_name = "cmvolume"

        # Verify ConfigMap
        command = f"kubectl get configmap {configmap_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)
        configmap_data = json.loads(result)
        
        assert configmap_data["data"]["var8"] == value1, "Incorrect value for 'var8'."
        assert configmap_data["data"]["var9"] == value2, "Incorrect value for 'var9'."
        logging.info(
            "ConfigMap '%s' has the correct values for 'var8' and 'var9'.",
            configmap_name,
        )

    def test_002_check_pod_details(self, json_input):
        logging.debug("Starting test_002_check_pod_details")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
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

        # Verify volume and ConfigMap mount
        volumes = [
            v for v in pod_data["spec"]["volumes"] if v["name"] == "config-volume"
        ]
        assert len(volumes) == 1, "Volume 'config-volume' not found in Pod."
        assert (
            volumes[0]["configMap"]["name"] == "cmvolume"
        ), "ConfigMap 'cmvolume' not found in volume."

        # Verify mount path
        volume_mounts = pod_data["spec"]["containers"][0]["volumeMounts"]
        config_mount = [vm for vm in volume_mounts if vm["name"] == "config-volume"]
        assert len(config_mount) == 1, "Volume mount 'config-volume' not found."
        assert config_mount[0]["mountPath"] == "/etc/lala", "Incorrect mountPath for config-volume."

        logging.info(
            "Pod '%s' has the correct volume with ConfigMap 'cmvolume'.", pod_name
        )
