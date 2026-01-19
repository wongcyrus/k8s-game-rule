import json
import logging
import time

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command


class TestCheck:
    def test_001_check_pod_creation(self, json_input):
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        pod_name = "busybox-pod"

        logging.info("Using namespace: %s", namespace)
        logging.info(
            "Checking if Pod '%s' is created in namespace '%s'",
            pod_name,
            namespace,
        )

        command = f"kubectl get pod {pod_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)
        
        if "error" in result.lower() or "not found" in result.lower():
            assert False, f"Pod '{pod_name}' not found in namespace '{namespace}'"
        
        pod_data = json.loads(result)
        assert pod_data["metadata"]["name"] == pod_name, f"Pod name mismatch"
        logging.info("Pod '%s' found in namespace '%s'", pod_name, namespace)

    def test_002_check_pod_logs(self, json_input):
        logging.debug("Starting test_002_check_pod_logs")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        pod_name = "busybox-pod"

        logging.info("Using namespace: %s", namespace)
        logging.info(
            "Checking logs for Pod '%s' in namespace '%s' using kubectl",
            pod_name,
            namespace,
        )

        # Wait for Pod to fully start
        time.sleep(7)

        # Use kubectl to get Pod logs
        command = f"kubectl logs {pod_name} -n {namespace} --tail=10"
        result = run_kubectl_command(kube_config, command)

        # Check log output
        logs = result
        logging.info("Logs for Pod '%s':\n%s", pod_name, logs)
        assert "0: " in logs, "Expected log output not found."
