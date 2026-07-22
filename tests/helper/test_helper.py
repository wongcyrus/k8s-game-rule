import inspect
import logging
import os

from jinja2 import Environment

from tests.helper.kubectrl_helper import build_kube_config, run_kubectl_command


def _deploy_generic(json_input, template_file, generated_file, caller_folder):
    ca_file = json_input.get("ca_file")
    kube_config = build_kube_config(
        json_input["cert_file"], json_input["key_file"], json_input["host"], ca_file
    )

    template_path = os.path.join(caller_folder, template_file)
    yaml_path = os.path.join(caller_folder, generated_file)

    env = Environment()
    jinja_template = env.from_string(open(template_path, "r", encoding="utf-8").read())

    with open(template_path, "r", encoding="utf-8") as file:
        yaml_content = jinja_template.render(json_input)
        with open(yaml_path, "w", encoding="utf-8") as file:
            file.write(yaml_content)

    command = f"kubectl apply -f {yaml_path}"
    result = run_kubectl_command(kube_config, command, check=True)
    logging.info(result)


def deploy_answer(json_input):
    caller_folder = os.path.dirname(os.path.abspath(inspect.stack()[1].filename))
    _deploy_generic(
        json_input, "answer.template.yaml", "answer.gen.yaml", caller_folder
    )


def deploy_setup(json_input):
    caller_folder = os.path.dirname(os.path.abspath(inspect.stack()[1].filename))
    _deploy_generic(json_input, "setup.template.yaml", "setup.gen.yaml", caller_folder)
