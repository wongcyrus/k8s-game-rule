import json
import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command


class TestCheck:
    def test_001_check_resourcequota_kubectl(self, json_input):
        logging.debug("Starting test_001_check_resourcequota_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        resourcequota_name = "resource-quota"

        logging.info(f"Using namespace: {namespace}")
        logging.info(f"Checking ResourceQuota '{resourcequota_name}' in namespace '{namespace}' using kubectl")

        # Use kubectl to get ResourceQuota
        command = (
            f"kubectl get resourcequota {resourcequota_name} -n {namespace} -o json"
        )
        result = run_kubectl_command(kube_config, command)

        # Parse kubectl output JSON
        resourcequota = json.loads(result)

        # Verify ResourceQuota content
        assert resourcequota["apiVersion"] == "v1", "Incorrect apiVersion."
        assert resourcequota["kind"] == "ResourceQuota", "Incorrect kind."
        assert (
            resourcequota["metadata"]["name"] == resourcequota_name
        ), "Incorrect metadata.name."

        # Verify hard limits in ResourceQuota
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

    def test_002_check_pod_kubectl(self, json_input):
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        namespace = json_input["namespace"]
        pod_name = "resource-pod"

        logging.info(
            "Checking Pod '%s' in namespace '%s' using kubectl", pod_name, namespace
        )

        # Use kubectl to get Pod
        command = f"kubectl get pod {pod_name} -n {namespace} -o json"
        result = run_kubectl_command(kube_config, command)

        # Parse kubectl output JSON
        pod = json.loads(result)

        # Verify Pod content
        assert pod["apiVersion"] == "v1", "Incorrect apiVersion."
        assert pod["kind"] == "Pod", "Incorrect kind."
        assert pod["metadata"]["name"] == pod_name, "Incorrect metadata.name."

        # Verify resource requests and limits in Pod
        resources = pod["spec"]["containers"][0]["resources"]
        cpu_request = resources["requests"]["cpu"]
        memory_request = resources["requests"]["memory"]
        cpu_limit = resources["limits"]["cpu"]
        memory_limit = resources["limits"]["memory"]

        assert cpu_request in [
            "0.5",
            "500m",
        ], f"Expected requests.cpu to be '0.5' or '500m', but got '{cpu_request}'."
        assert (
            memory_request == "1Gi"
        ), f"Expected requests.memory to be '1Gi', but got '{memory_request}'."
        assert (
            cpu_limit == "1"
        ), f"Expected limits.cpu to be '1', but got '{cpu_limit}'."
        assert (
            memory_limit == "2Gi"
        ), f"Expected limits.memory to be '2Gi', but got '{memory_limit}'."

        logging.info("Pod '%s' has the correct resource requests and limits.", pod_name)
