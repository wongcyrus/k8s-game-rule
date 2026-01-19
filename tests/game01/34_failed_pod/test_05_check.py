import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command


class TestCheck:
    def test_001_check_pod_absence(self, json_input):
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        pod_name = "fail-pod"
        namespace = "one"

        command = f"kubectl get pod {pod_name} -n {namespace}"
        result = run_kubectl_command(kube_config, command)
        
        # Pod should not exist, so we expect an error message
        if "NotFound" in result or "not found" in result.lower():
            logging.info(f"Pod '{pod_name}' does not exist as expected.")
        else:
            assert False, f"Pod '{pod_name}' should not have been created, but it exists."
