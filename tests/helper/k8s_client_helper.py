from pathlib import Path

from kubernetes import client
from kubernetes.config import load_kube_config


def configure_k8s_client(json_input):
    kubeconfig_path = json_input.get("kubeconfig_file")
    if not kubeconfig_path:
        raise RuntimeError("json_input must include kubeconfig_file; only config.yaml is supported")
    load_kube_config(config_file=kubeconfig_path)
    return client.CoreV1Api()
