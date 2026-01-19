import logging

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command

class TestCheck:

    def test_001_pod_exists_with_kubectl(self, json_input):
        kube_config = build_kube_config(
            json_input["cert_file"], json_input["key_file"], json_input["host"]
        )
        command = "kubectl get pods -n default"
        result = run_kubectl_command(kube_config, command)
        logging.info(result)
        pod_name = "nginx"
        assert (
            pod_name in result
        ), f"Pod '{pod_name}' does not exist in namespace 'default'"
