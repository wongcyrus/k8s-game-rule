import logging
import os
import json
import subprocess
import tempfile
from pathlib import Path

from jinja2 import Environment


def _resolve_ca_path(client_certificate, ca_certificate=None):
    if ca_certificate:
        return ca_certificate

    candidate = Path(client_certificate).with_name("ca.crt")
    if candidate.exists():
        return str(candidate)

    return None


def build_kube_config(client_certificate=None, client_key=None, endpoint=None, ca_certificate=None, bearer_token=None):
    cert_data = client_certificate
    key_data = client_key
    ca_data = _resolve_ca_path(client_certificate, ca_certificate) if client_certificate else ca_certificate

    template = """
apiVersion: v1
kind: Config
clusters:
  - name: k8s-cluster
    cluster:
      server: {{endpoint}}
{% if ca_data %}
      certificate-authority: {{ca_data}}
{% endif %}
contexts:
  - name: k8s-context
    context:
      cluster: k8s-cluster
      user: k8s-user
current-context: k8s-context
users:
  - name: k8s-user
    user:
{% if bearer_token %}
      token: {{bearer_token}}
{% else %}
      client-certificate: {{cert_data}}
      client-key: {{key_data}}
{% endif %}
    """
    env = Environment()
    jinja_template = env.from_string(template)
    return jinja_template.render(
        endpoint=endpoint, cert_data=cert_data, key_data=key_data, ca_data=ca_data, bearer_token=bearer_token
    ).encode("utf-8")


def run_kubectl_command(kube_config, command):
    with tempfile.NamedTemporaryFile(delete=False) as temp_config:
        temp_config.write(kube_config)
        temp_config.flush()
        os.environ["KUBECONFIG"] = temp_config.name
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as e:
            logging.info(e.stderr)
            return e.stderr
    return result.stdout


def run_kubectl_json_command(kube_config, command):
    result = run_kubectl_command(kube_config, command)
    return json.loads(result)


def build_kube_config_from_input(json_input):
    if json_input.get("kubeconfig_file"):
        with open(json_input["kubeconfig_file"], "rb") as kubeconfig_file:
            return kubeconfig_file.read()

    if json_input.get("bearer_token"):
        return build_kube_config(
            endpoint=json_input["host"],
            ca_certificate=json_input.get("ca_file"),
            bearer_token=json_input["bearer_token"],
        )

    return build_kube_config(
        json_input["cert_file"], json_input["key_file"], json_input["host"]
    )


def delete_namespace(json_input):
    kube_config = build_kube_config_from_input(json_input)

    pod_namespace = json_input["namespace"]
    command = f"kubectl delete namespace  {pod_namespace}"
    result = run_kubectl_command(kube_config, command)
    logging.info(result)
