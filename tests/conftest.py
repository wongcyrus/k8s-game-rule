import base64
import json
import logging
import os
import random
import subprocess
import time

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
    """
    Provides test input data from multiple sources:
    1. Lambda mode: Reads from /tmp/json_input.json (created by TestRunner)
    2. Local mode: Reads from session.json files with Jinja2 rendering
    """
    # Lambda mode: for running in AWS Lambda via TestRunner
    if os.path.exists("/tmp/json_input.json"):
        with open("/tmp/json_input.json", "r", encoding="utf-8") as file:
            json_str_input = file.read()
            result = json.loads(json_str_input)
        return result

    # Local mode: for local testing with minikube/local k8s cluster
    test_path_name = request.path
    folder_path = os.path.dirname(test_path_name)

    # Read endpoint from local file
    endpoint_file_path = os.path.join(
        os.path.dirname(os.path.dirname(folder_path)),
        "k8s-configure",
        "endpoint.txt"
    )
    
    if os.path.exists(endpoint_file_path):
        with open(endpoint_file_path, "r", encoding="utf-8") as endpoint_file:
            host = endpoint_file.read().strip()
    else:
        # Fallback to default minikube endpoint
        host = "https://127.0.0.1:8443"
    
    result = {
        "cert_file": "~/.minikube/profiles/minikube/client.crt",
        "key_file": "~/.minikube/profiles/minikube/client.key",
        "ca_file": "~/.minikube/ca.crt",
        "host": host,
    }

    # Load session.json template and render with Jinja2
    session_json_file = os.path.join(folder_path, "session.json")
    test_name = os.path.splitext(os.path.basename(test_path_name))[0]
    task_session_file = os.path.join(folder_path, f"{test_name}.json")

    logging.info(f"Loading session from: {session_json_file}")
    if os.path.exists(session_json_file):
        with open(session_json_file, "r", encoding="utf-8") as file:
            session_json = json.load(file)
            
            # Merge with test-specific session file if exists
            if os.path.exists(task_session_file):
                with open(task_session_file, "r", encoding="utf-8") as file1:
                    task_session = json.load(file1)
                    session_json.update(task_session)

            # Render Jinja2 templates in session values
            for key, value in session_json.items():
                if isinstance(value, str):
                    session_json[key] = render(value)
            
            logging.info(f"Rendered session: {session_json}")
        result.update(session_json)
    
    return result


@pytest.fixture(autouse=True)
def delay_after_answer(request):

    # Lambda mode: for running in AWS Lambda via TestRunner
    if os.path.exists("/tmp/json_input.json"):
        yield  # Test runs here
        return
    
    test_file = os.path.basename(request.path)

    if test_file == "test_01_setup.py":
        logging.info("Running minikube start before test_01_setup.py...")
        subprocess.run(
            [
                "minikube",
                "start",
                "--driver=docker",
                "--listen-address=127.0.0.1",
                "--apiserver-names=localhost",
                "--ports=127.0.0.1:8443:8443",
            ],
            check=True,
            timeout=300,
        )
        time.sleep(10)  # Wait for minikube to be fully up and running

    """Inject a 30-second delay after test_03_answer.py tests"""
    yield  # Test runs here
    

    if test_file == "test_03_answer.py":
        logging.info("Waiting 30 seconds after running test_03_answer.py...")
        time.sleep(30)

    if test_file == "test_06_cleanup.py":
        logging.info("Running minikube delete after test_06_cleanup.py...")
        subprocess.run(["minikube", "delete"], check=True, timeout=120)


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
