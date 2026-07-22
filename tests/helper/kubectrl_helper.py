import logging
import os
import subprocess
import tempfile
import json

from jinja2 import Environment


class KubectlCommandError(RuntimeError):
    def __init__(self, command, stderr, returncode):
        self.command = command
        self.stderr = stderr
        self.returncode = returncode
        super().__init__(stderr or f"kubectl command failed: {command}")


def build_kube_config(client_certificate, client_key, endpoint, ca_certificate=None):
    cert_data = os.path.expanduser(client_certificate)
    key_data = os.path.expanduser(client_key)

    if ca_certificate:
        ca_data = os.path.expanduser(ca_certificate)
        template = """
apiVersion: v1
kind: Config
clusters:
  - name: k8s-cluster
    cluster:
      server: {{endpoint}}
      certificate-authority: {{ca_data}}
contexts:
  - name: k8s-context
    context:
      cluster: k8s-cluster
      user: k8s-user
current-context: k8s-context
users:
  - name: k8s-user
    user:
      client-certificate: {{cert_data}}
      client-key: {{key_data}}
    """
    else:
        template = """
apiVersion: v1
kind: Config
clusters:
  - name: k8s-cluster
    cluster:
      server: {{endpoint}}
      insecure-skip-tls-verify: true
contexts:
  - name: k8s-context
    context:
      cluster: k8s-cluster
      user: k8s-user
current-context: k8s-context
users:
  - name: k8s-user
    user:
      client-certificate: {{cert_data}}
      client-key: {{key_data}}
    """
    
    env = Environment()
    jinja_template = env.from_string(template)
    return jinja_template.render(
        endpoint=endpoint, cert_data=cert_data, key_data=key_data, ca_data=ca_data if ca_certificate else None
    ).encode("utf-8")


def run_kubectl_command(kube_config, command, check=False):
    with tempfile.NamedTemporaryFile(delete=False) as temp_config:
        temp_config.write(kube_config)
        temp_config.flush()
        os.environ["KUBECONFIG"] = temp_config.name
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, check=False
            )
        finally:
            try:
                os.unlink(temp_config.name)
            except FileNotFoundError:
                pass

    if result.returncode != 0:
        error_output = result.stderr or result.stdout
        logging.info(error_output)
        if check:
            raise KubectlCommandError(command, error_output, result.returncode)
        return error_output

    return result.stdout


def run_kubectl_json_command(kube_config, command, check=True):
    return json.loads(run_kubectl_command(kube_config, command, check=check))


def delete_namespace(json_input):
    ca_file = json_input.get("ca_file")
    kube_config = build_kube_config(
        json_input["cert_file"], json_input["key_file"], json_input["host"], ca_file
    )

    pod_namespace = json_input["namespace"]
    command = f"kubectl delete namespace  {pod_namespace}"
    result = run_kubectl_command(kube_config, command)
    logging.info(result)
