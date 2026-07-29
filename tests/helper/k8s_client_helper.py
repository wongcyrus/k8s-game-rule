from pathlib import Path

from kubernetes import client
from kubernetes.config import load_kube_config


def configure_k8s_client(json_input):
    if json_input.get("kubeconfig_file"):
        load_kube_config(config_file=json_input["kubeconfig_file"])
        return client.CoreV1Api()

    client_configuration = client.Configuration()
    client_configuration.host = json_input["host"]
    if json_input.get("bearer_token"):
        client_configuration.api_key = {"authorization": f"Bearer {json_input['bearer_token']}"}
    else:
        client_configuration.cert_file = json_input["cert_file"]
        client_configuration.key_file = json_input["key_file"]
    ca_file = json_input.get("ca_file")
    if not ca_file and json_input.get("cert_file"):
        candidate = Path(json_input["cert_file"]).with_name("ca.crt")
        if candidate.exists():
            ca_file = str(candidate)
    if ca_file:
        client_configuration.ssl_ca_cert = ca_file
    client.Configuration.set_default(client_configuration)
    return client.CoreV1Api()
