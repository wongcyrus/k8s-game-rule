import base64
import json
import logging
import os
import random
from pathlib import Path

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


def load_session_from_dynamodb(table, email, game, task):
    response = table.get_item(
        Key={
            "email": email,
            "gameTask": f"{game}#{task}",
        }
    )
    item = response.get("Item")
    if item and "session_data" in item:
        return item["session_data"]

    response = table.get_item(
        Key={
            "email": email,
            "game": f"{game}#{task}",
        }
    )
    item = response.get("Item")
    if item and "session" in item:
        return json.loads(item["session"])

    return None


REPO_ROOT = Path(__file__).resolve().parent.parent
K8S_CONFIGURE_DIR = REPO_ROOT / "k8s-configure"
KUBECONFIG_PATH = K8S_CONFIGURE_DIR / "config.yaml"


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
            session = load_session_from_dynamodb(
                table,
                os.environ["EMAIL"],
                game,
                task,
            )
            if session is None:
                raise RuntimeError(
                    f"No task session found in {os.environ['SESSION_TABLE_NAME']} "
                    f"for email={os.environ['EMAIL']} and task={game}#{task}"
                )

            K8S_CONFIGURE_DIR.mkdir(parents=True, exist_ok=True)
            kubeconfig = session.get("$kubeconfig")
            if not kubeconfig:
                raise RuntimeError(
                    "SESSION_FROM_DYNAMODB=True requires session data to include $kubeconfig"
                )
            with open(KUBECONFIG_PATH, "w", encoding="utf-8") as kubeconfig_file:
                kubeconfig_file.write(kubeconfig)
            result = {"kubeconfig_file": str(KUBECONFIG_PATH)}
            result.update(session)
            return result
        else:
            if not KUBECONFIG_PATH.exists():
                raise RuntimeError(
                    f"Local testing requires kubeconfig file: {KUBECONFIG_PATH}"
                )
            result = {"kubeconfig_file": str(KUBECONFIG_PATH)}

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
