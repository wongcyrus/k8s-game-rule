import os

from kubernetes import client


def configure_k8s_client(json_input):
    client_configuration = client.Configuration()
    client_configuration.host = json_input["host"]
    client_configuration.cert_file = os.path.expanduser(json_input["cert_file"])
    client_configuration.key_file = os.path.expanduser(json_input["key_file"])
    
    # Add CA certificate if provided, otherwise disable SSL verification
    if "ca_file" in json_input and json_input["ca_file"]:
        client_configuration.ssl_ca_cert = os.path.expanduser(json_input["ca_file"])
    else:
        client_configuration.verify_ssl = False
    
    client.Configuration.set_default(client_configuration)
    return client.CoreV1Api()
