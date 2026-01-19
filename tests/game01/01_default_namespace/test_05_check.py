import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:
    def test_001_namespace_exists_with_kubectl(self, json_input):
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        command = "kubectl get namespace"
        result = run_kubectl_command(kube_config, command)
        logging.info(result)
        namespace = "default"
        assert namespace in result, f"Namespace '{namespace}' does not exist"
