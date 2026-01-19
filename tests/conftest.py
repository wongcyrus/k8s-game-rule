import base64
import json
import logging
import os
import random

import boto3
import pytest
from jinja2 import Environment
from names_generator import generate_name


def random_name(seed: int = 0) -> str:
    return generate_name(style="underscore", seed=seed).replace("_", "")


def random_number(from_number: int, to_number: int) -> str:
    return str(random.randint(from_number, to_number))


def base64_encode(value: str) -> str:
    return base64.b64encode(value.encode()).decode()


func_dict = {
    "student_id": lambda: "123456789",
    "random_name": random_name,
    "random_number": random_number,
    "base64_encode": base64_encode,
}


def render(template):
    env = Environment()
    jinja_template = env.from_string(template)
    jinja_template.globals.update(func_dict)
    template_string = jinja_template.render()
    return template_string


@pytest.fixture(scope="module", autouse=True)
def json_input(request):
    # for local testing
    if not os.path.exists("/tmp/json_input.json"):
        test_path_name = request.path
        folder_path = os.path.dirname(test_path_name)

        session_from_dynamodb = os.getenv("SESSION_FROM_DYNAMODB") == "True"
        if session_from_dynamodb:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table(os.environ["SESSION_TABLE_NAME"])
            task = os.path.basename(folder_path)
            game = os.path.basename(os.path.dirname(folder_path))
            response = table.get_item(
                Key={
                    "email": os.environ["EMAIL"],
                    "game": f"{game}#{task}",
                }
            )
            if "Item" in response:
                session = json.loads(response["Item"]["session"])
                client_certificate = session["$client_certificate"]
                client_key = session["$client_key"]
                host = session["$endpoint"]
                with open(
                    "/workspaces/k8s-game-rule/k8s-configure/client.crt",
                    "w",
                    encoding="utf-8",
                ) as cert_file:
                    cert_file.write(client_certificate)
                with open(
                    "/workspaces/k8s-game-rule/k8s-configure/client.key",
                    "w",
                    encoding="utf-8",
                ) as key_file:
                    key_file.write(client_key)

                result = {
                    "cert_file": "/workspaces/k8s-game-rule/k8s-configure/client.crt",
                    "key_file": "/workspaces/k8s-game-rule/k8s-configure/client.key",
                    "host": host,
                }
                result.update(session)
                return result
        else:
            with open(
                "/home/developer/Documents/data-disk/k8s-game-rule/k8s-configure/endpoint.txt",
                "r",
                encoding="utf-8",
            ) as endpoint_file:
                host = endpoint_file.read().strip()
            result = {
                "cert_file": "~/.minikube/profiles/minikube/client.crt",
                "key_file": "~/.minikube/profiles/minikube/client.key",
                "ca_file": "~/.minikube/ca.crt",
                "host": host,
            }

            session_json_file = os.path.join(folder_path, "session.json")
            test_name = os.path.splitext(os.path.basename(test_path_name))[0]
            task_session_file = os.path.join(folder_path, f"{test_name}.json")

            logging.info(task_session_file)
            if os.path.exists(session_json_file):
                with open(session_json_file, "r", encoding="utf-8") as file:
                    session_json = json.load(file)
                    if os.path.exists(task_session_file):
                        with open(task_session_file, "r", encoding="utf-8") as file1:
                            task_session = json.load(file1)
                            session_json.update(task_session)

                    for key, value in session_json.items():
                        if isinstance(value, str):
                            session_json[key] = render(value)
                    logging.info(session_json)
                result.update(session_json)
            return result

    # for running in AWS lambda
    with open("/tmp/json_input.json", "r", encoding="utf-8") as file:
        json_str_input = file.read()
        result = json.loads(json_str_input)
    return result


def pytest_collection_modifyitems(config, items):  # disable=W0613
    skip = pytest.mark.skip(reason="Skip Answer")
    skip_answer = os.getenv("SKIP_ANSWER_TESTS") == "True"
    if skip_answer:
        for item in items:
            logging.info(item.path)
            if "answer" in item.name:
                item.add_marker(skip)

    sorted_items = items.copy()

    sorted_items.sort(
        key=lambda item: (os.path.dirname(item.path), os.path.basename(item.path))
    )
    items[:] = sorted_items
