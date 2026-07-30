# k8s-game-rule

Kubernetes Isekai (異世界) is an open-source RPG designed for hands-on Kubernetes learning through gamification. Ideal for junior to Higher Diploma students of Hong Kong Institute of Information Technology (HKIIT), it transforms Kubernetes education into an engaging adventure.

1. Role-Playing Adventure: Students interact with NPCs who assign Kubernetes tasks.
2. Task-Based Learning: Tasks involve setting up and managing Kubernetes clusters.
3. Free Access: Uses AWS Academy Learner Lab with Minikube or Kubernetes.
4. Scalable Grading: AWS SAM application tests Kubernetes setups within AWS Lambda.
5. Progress Tracking: Students track progress and earn rewards.
6. This game offers practical Kubernetes experience in a fun, cost-effective way.
7. GenAI Chat: Integrates Generative AI to make NPC interactions more dynamic and fun, enhancing the overall learning experience.

This repository is the template to define the game task.

## Demo

[![#Kubernetes Isekai (Alpha) -  free #k8s #rpggame with free #awsacademy learner lab](https://img.youtube.com/vi/dIwNWwz681k/0.jpg)](https://youtu.be/dIwNWwz681k)

## Local Development

To enable auto-completion 
1. Run ```./create_virtural_env.sh```
2. Set Python Interpreter to ```/workspaces/k8s-game-rule/venv/bin/python```

If VS Code's testing explorer behaves unexpectedly, such as after a folder rename, clear the Python cache.
```./clean_python_cache.sh ```

## To skip answer
Change .env 
```
SKIP_ANSWER_TESTS=True
```

## For Game Testing
You can load the session from AWS DynamoDB.
Set the token with CLI.
Region us-east-1 and output json
```
aws configure
aws configure set aws_session_token <Session Token>
```

Change .env 
```
SESSION_FROM_DYNAMODB=True
SESSION_TABLE_NAME=k8s-grader-api-dev-TaskStateTable-XXXX
EMAIL=abcd@vtc.edu.hk
```
SESSION_TABLE_NAME is the grader TaskStateTable. The local test loader reads
task session data from `session_data` using the DynamoDB key
`email + gameTask` (for example `game02#087_kustomize_configuration`).
EMAIL is the testing account email.

## Running test in command line
Run all tasks
```
pytest --import-mode=importlib --rootdir=.
```
Run single task
```
pytest --import-mode=importlib --rootdir=. tests/game01/02_create_namespace/
```
To skip answer test
```
SKIP_ANSWER_TESTS=True pytest --import-mode=importlib --rootdir=.
```

## Running each task on a fresh local Minikube
Use the fresh-cluster runner when you want authoring behavior closer to test generation, where each task starts from a clean cluster.

Dry-run the task selection and output plan:
```bash
python3 tools/run_tasks_fresh_minikube.py --game game02 --dry-run
```

Run one task with a fresh Minikube profile:
```bash
python3 tools/run_tasks_fresh_minikube.py --game game02 --task 087_sidecar_containers
```

Run a range of tasks and skip answer tests:
```bash
python3 tools/run_tasks_fresh_minikube.py --game game02 --from-task 087_sidecar_containers --to-task 201_pod_restart_policies --skip-answer
```

The runner will:
1. Start a new Minikube profile for each task
2. Write `k8s-configure/config.yaml` and `k8s-configure/endpoint.txt`
3. Clear Python caches under `tests/` before the run, and clear task-local caches again before each task
4. Run `pytest --import-mode=importlib --rootdir=. tests/<game>/<task>`
5. Restore the previous `k8s-configure/config.yaml` and `k8s-configure/endpoint.txt` after the run finishes
6. Save logs and JSON summaries under `.artifacts/minikube-fresh-runs/<timestamp>/`
7. Delete the Minikube profile unless `--keep-on-fail` is used

This extra cache cleanup is important after moving task folders between games, because stale `__pycache__` entries can preserve old source paths and break helpers that rely on `inspect.stack()`.

This local runner behavior is different from the AWS Lambda grader path: Lambda does not clear `__pycache__` explicitly, but it clears the managed `/tmp/<game>` extracted test tree before execution, which removes stale task-local bytecode as part of deleting the whole game directory.

If you already created the repo virtualenv with `./create_virtural_env.sh`, the runner will use `./venv/bin/pytest` automatically.

Install Kubectl command tools for Unit Test
https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/

1. Put your cluster kubeconfig in `k8s-configure/config.yaml`.
2. For local minikube, ensure that kubeconfig points at the local API server.

## Core Developers

Students from [Higher Diploma in Cloud and Data Centre Administration](https://www.vtc.edu.hk/admission/en/programme/it114115-higher-diploma-in-cloud-and-data-centre-administration/)

- [錢弘毅](https://www.linkedin.com/in/hongyi-qian-a71b17290/)
- [Ho Chun Sun Don (何俊申)](https://www.linkedin.com/in/ho-chun-sun-don-%E4%BD%95%E4%BF%8A%E7%94%B3-660a94290/)
- [Kit Fong Loo](https://www.linkedin.com/in/kit-fong-loo-910482347/)
- [Yuehan WU](https://www.linkedin.com/in/yuehan-wu-a40612290/)
