# test_05_check.py
import logging
import pytest
import json
from subprocess import CalledProcessError
from tests.helper.k8s_client_helper import configure_k8s_client
from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

@pytest.mark.order(5)
class TestCheck:
    def test_001_check_label_removed_with_library(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        pod_namespace = json_input["namespace"]
        
        pod_names = ["nginx1", "nginx2", "nginx3"]

        for pod_name in pod_names:
            try:
                pod = k8s_client.read_namespaced_pod(name=pod_name, namespace=pod_namespace)
                assert "app" not in pod.metadata.labels, f"Pod '{pod_name}' still has the label 'app'"
                logging.info(f"Pod '{pod_name}' does not have the label 'app'")
            except ApiException as e:
                if e.status == 404:
                    logging.info(f"Pod '{pod_name}' not found, skipping check.")
                else:
                    raise

    def test_002_verify_label_removed_with_kubectl(self, json_input):
        logging.debug("Starting test_002_verify_label_removed_with_kubectl")
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        
        pod_namespace = json_input["namespace"]
        pod_names = ["nginx1", "nginx2", "nginx3"]

        for pod_name in pod_names:
            try:
                command = f"kubectl get pod {pod_name} -n {pod_namespace} -o json"
                logging.debug(f"Running command: {command}")
                result = run_kubectl_command(kube_config, command)
                logging.debug(f"Command result: {result}")
                
                json_output = result.strip()
                logging.debug(f"Command output: {json_output}")
                logging.info(json_output)
            
                pod_data = json.loads(json_output)
                assert "app" not in pod_data["metadata"]["labels"], f"Pod '{pod_name}' still has the label 'app'"
                logging.info(f"Pod '{pod_name}' does not have the label 'app'")
            except CalledProcessError as e:
                if 'not found' in str(e):
                    logging.info(f"Pod '{pod_name}' not found, skipping check.")
                else:
                    raise
