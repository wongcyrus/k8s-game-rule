import logging

from tests.helper.kubectrl_helper import build_kube_config_from_input, run_kubectl_command


class TestCleanup:

    def test_cleanup(self, json_input):
        kube_config = build_kube_config_from_input(json_input)
        namespace = json_input["namespace"]
        command = f"kubectl delete namespace {namespace}"
        result = run_kubectl_command(kube_config, command)
        logging.info(result)
