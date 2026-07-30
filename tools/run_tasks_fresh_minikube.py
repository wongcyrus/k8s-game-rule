#!/usr/bin/env python3
"""Run task directories against a fresh Minikube profile per task."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_ROOT = REPO_ROOT / "tests"
K8S_CONFIGURE_DIR = REPO_ROOT / "k8s-configure"
KUBECONFIG_PATH = K8S_CONFIGURE_DIR / "config.yaml"
ENDPOINT_PATH = K8S_CONFIGURE_DIR / "endpoint.txt"
DEFAULT_ARTIFACT_ROOT = REPO_ROOT / ".artifacts" / "minikube-fresh-runs"


@dataclass
class TaskResult:
    game: str
    task: str
    profile: str
    exit_code: int
    duration_seconds: float
    counts: dict[str, int]
    failed_tests: list[str]
    failed_phases: list[str]
    signals: list[str]
    log_file: str
    summary_file: str
    kept_profile: bool
    task_path: str


@dataclass
class LocalAccessSnapshot:
    kubeconfig_exists: bool
    kubeconfig_text: str
    endpoint_exists: bool
    endpoint_text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Start a fresh Minikube profile for each task and run pytest for that task only."
    )
    parser.add_argument("--game", required=True, help="Game folder under tests/, for example game02")
    parser.add_argument(
        "--task",
        action="append",
        default=[],
        help="Specific task folder to run. Repeat to pass multiple tasks.",
    )
    parser.add_argument("--from-task", dest="from_task", default="", help="Inclusive start task")
    parser.add_argument("--to-task", dest="to_task", default="", help="Inclusive end task")
    parser.add_argument(
        "--batch-file",
        default="",
        help="Text file containing one task folder per line. Blank lines and # comments are ignored.",
    )
    parser.add_argument(
        "--artifact-dir",
        default="",
        help="Artifact output directory. Defaults to .artifacts/minikube-fresh-runs/<timestamp>/",
    )
    parser.add_argument(
        "--profile-prefix",
        default="fresh",
        help="Prefix for generated Minikube profile names.",
    )
    parser.add_argument("--driver", default="docker", help="Minikube driver, for example docker.")
    parser.add_argument("--cpus", type=int, default=4, help="CPUs to allocate per Minikube profile.")
    parser.add_argument("--memory", default="8192", help="Memory for Minikube, for example 8192 or 8g.")
    parser.add_argument(
        "--kubernetes-version",
        default="",
        help="Optional Kubernetes version passed to minikube start.",
    )
    parser.add_argument(
        "--delete-timeout",
        type=int,
        default=120,
        help="Timeout in seconds for minikube delete.",
    )
    parser.add_argument(
        "--start-timeout",
        type=int,
        default=480,
        help="Wait timeout in seconds for minikube start.",
    )
    parser.add_argument(
        "--listen-address",
        default="127.0.0.1",
        help="listen-address passed to minikube start.",
    )
    parser.add_argument(
        "--apiserver-name",
        default="localhost",
        help="apiserver-names passed to minikube start.",
    )
    parser.add_argument(
        "--publish-port",
        default="127.0.0.1:8443:8443",
        help="ports value passed to minikube start.",
    )
    parser.add_argument(
        "--keep-on-fail",
        action="store_true",
        help="Keep the failing Minikube profile for inspection and stop the run after the failure.",
    )
    parser.add_argument(
        "--skip-answer",
        action="store_true",
        help="Set SKIP_ANSWER_TESTS=True while running pytest.",
    )
    parser.add_argument(
        "--pytest-exe",
        default="",
        help="Explicit pytest executable. Defaults to ./venv/bin/pytest when present.",
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        help="Rerun tasks even if a summary JSON already exists in the artifact directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Resolve tasks and print the plan without starting Minikube or pytest.",
    )
    return parser.parse_args()


def ensure_command(name: str) -> None:
    if shutil.which(name):
        return
    raise RuntimeError(f"Required command not found in PATH: {name}")


def resolve_pytest_executable(explicit: str) -> list[str]:
    if explicit:
        return [explicit]
    repo_pytest = REPO_ROOT / "venv" / "bin" / "pytest"
    if repo_pytest.exists():
        return [str(repo_pytest)]
    discovered = shutil.which("pytest")
    if discovered:
        return [discovered]
    raise RuntimeError(
        "pytest executable not found. Create the repo virtualenv with ./create_virtural_env.sh "
        "or pass --pytest-exe explicitly."
    )


def resolve_pytest_for_manifest(explicit: str) -> list[str]:
    if explicit:
        return [explicit]
    repo_pytest = REPO_ROOT / "venv" / "bin" / "pytest"
    if repo_pytest.exists():
        return [str(repo_pytest)]
    discovered = shutil.which("pytest")
    if discovered:
        return [discovered]
    return ["pytest"]


def load_batch_file(path_str: str) -> list[str]:
    if not path_str:
        return []
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise ValueError(f"Batch file not found: {path}")
    items: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        items.append(line)
    return items


def discover_tasks(game: str) -> list[str]:
    game_dir = TESTS_ROOT / game
    if not game_dir.exists():
        raise ValueError(f"Game folder not found: {game_dir}")
    tasks = sorted(
        path.name
        for path in game_dir.iterdir()
        if path.is_dir() and any(path.glob("test_*.py"))
    )
    if not tasks:
        raise ValueError(f"No task folders found under {game_dir}")
    return tasks


def apply_task_filters(tasks: list[str], args: argparse.Namespace) -> list[str]:
    selected = tasks
    explicit_tasks = list(dict.fromkeys(args.task + load_batch_file(args.batch_file)))
    if explicit_tasks:
        unknown = [task for task in explicit_tasks if task not in tasks]
        if unknown:
            raise ValueError(f"Unknown task(s): {', '.join(unknown)}")
        selected = [task for task in tasks if task in explicit_tasks]
    if args.from_task:
        if args.from_task not in selected:
            raise ValueError(f"--from-task not found in selected tasks: {args.from_task}")
        selected = selected[selected.index(args.from_task):]
    if args.to_task:
        if args.to_task not in selected:
            raise ValueError(f"--to-task not found in selected tasks: {args.to_task}")
        selected = selected[: selected.index(args.to_task) + 1]
    if not selected:
        raise ValueError("No tasks selected after applying filters.")
    return selected


def artifact_dir_from_args(path_str: str) -> Path:
    if path_str:
        return Path(path_str).expanduser().resolve()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return DEFAULT_ARTIFACT_ROOT / timestamp


def profile_name(prefix: str, game: str, task: str) -> str:
    token = f"{prefix}-{game}-{task}".lower()
    token = re.sub(r"[^a-z0-9-]+", "-", token)
    token = re.sub(r"-{2,}", "-", token).strip("-")
    return token[:63]


def append_command(log_file: Path, title: str, command: list[str], *, env: dict[str, str] | None = None) -> None:
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {title}\n")
        handle.write("COMMAND: " + " ".join(command) + "\n")
        if env:
            handle.write("ENV: " + json.dumps(env, sort_keys=True) + "\n")


def clear_python_cache(root_dir: Path, log_file: Path, title: str) -> None:
    removed_paths: list[str] = []
    for pycache_dir in sorted(root_dir.rglob("__pycache__")):
        if pycache_dir.is_dir():
            shutil.rmtree(pycache_dir)
            removed_paths.append(str(pycache_dir.relative_to(REPO_ROOT)))

    for suffix in ("*.pyc", "*.pyo"):
        for compiled_file in sorted(root_dir.rglob(suffix)):
            if compiled_file.is_file():
                compiled_file.unlink()
                removed_paths.append(str(compiled_file.relative_to(REPO_ROOT)))

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {title}\n")
        handle.write(f"ROOT_DIR: {root_dir}\n")
        if removed_paths:
            handle.write("REMOVED:\n")
            for path in removed_paths:
                handle.write(path + "\n")
        else:
            handle.write("REMOVED: none\n")


def run_command(
    command: list[str],
    *,
    log_file: Path,
    title: str,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    append_command(log_file, title, command, env=env)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.flush()
        result = subprocess.run(
            command,
            cwd=str(cwd or REPO_ROOT),
            env=env,
            stdout=handle,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=timeout,
        )
        handle.write(f"\nEXIT_CODE={result.returncode}\n")
    if check and result.returncode != 0:
        raise RuntimeError(f"{title} failed with exit code {result.returncode}")
    return result


def write_local_kube_access(profile: str, log_file: Path) -> None:
    K8S_CONFIGURE_DIR.mkdir(parents=True, exist_ok=True)

    kubeconfig_yaml = subprocess.run(
        ["minikube", "-p", profile, "kubectl", "--", "config", "view", "--raw", "-o", "yaml"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\n## write kube access files\n")
        handle.write("COMMAND: minikube -p " + profile + " kubectl -- config view --raw -o yaml\n")
        handle.write(kubeconfig_yaml.stdout)
        handle.write(f"\nEXIT_CODE={kubeconfig_yaml.returncode}\n")
    if kubeconfig_yaml.returncode != 0:
        raise RuntimeError("Failed to fetch kubeconfig YAML from Minikube")
    KUBECONFIG_PATH.write_text(kubeconfig_yaml.stdout, encoding="utf-8")

    kubeconfig_json = subprocess.run(
        ["minikube", "-p", profile, "kubectl", "--", "config", "view", "--raw", "-o", "json"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write("\nCOMMAND: minikube -p " + profile + " kubectl -- config view --raw -o json\n")
        handle.write(kubeconfig_json.stdout)
        handle.write(f"\nEXIT_CODE={kubeconfig_json.returncode}\n")
    if kubeconfig_json.returncode != 0:
        raise RuntimeError("Failed to fetch kubeconfig JSON from Minikube")
    data = json.loads(kubeconfig_json.stdout)
    clusters = data.get("clusters") or []
    if not clusters:
        raise RuntimeError("Minikube kubeconfig JSON did not include clusters")
    server = clusters[0].get("cluster", {}).get("server", "")
    if not server:
        raise RuntimeError("Minikube kubeconfig JSON did not include cluster.server")
    ENDPOINT_PATH.write_text(server + "\n", encoding="utf-8")


def parse_counts(log_text: str) -> dict[str, int]:
    def pick(pattern: str) -> int:
        match = re.search(pattern, log_text)
        return int(match.group(1)) if match else 0

    return {
        "passed": pick(r"(\d+) passed"),
        "failed": pick(r"(\d+) failed"),
        "errors": pick(r"(\d+) error"),
        "skipped": pick(r"(\d+) skipped"),
        "xfailed": pick(r"(\d+) xfailed"),
    }


def parse_failed_tests(log_text: str) -> list[str]:
    return [line for line in log_text.splitlines() if line.startswith("FAILED ")]


def parse_failed_phases(failed_tests: Iterable[str]) -> list[str]:
    phases = []
    for line in failed_tests:
        if "/test_01_setup.py" in line:
            phases.append("setup")
        elif "/test_02_ready.py" in line:
            phases.append("ready")
        elif "/test_03_answer.py" in line:
            phases.append("answer")
        elif "/test_04_challenge.py" in line:
            phases.append("challenge")
        elif "/test_05_check.py" in line:
            phases.append("check")
        elif "/test_06_cleanup.py" in line:
            phases.append("cleanup")
        else:
            phases.append("other")
    return sorted(set(phases))


def detect_signals(log_text: str) -> list[str]:
    signals = []
    checks = {
        "timeout": r"TimeoutError|timed out",
        "pending": r"\bPending\b|ContainerCreating|CrashLoopBackOff|Init:",
        "not_found": r"not found|No resources found|does not exist",
        "unsupported_api": r"no matches for kind|unsupported|not supported",
        "not_ready": r"not ready|unavailable|failed to become ready|waiting for",
    }
    for name, pattern in checks.items():
        if re.search(pattern, log_text, re.IGNORECASE):
            signals.append(name)
    return signals


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def snapshot_local_access() -> LocalAccessSnapshot:
    return LocalAccessSnapshot(
        kubeconfig_exists=KUBECONFIG_PATH.exists(),
        kubeconfig_text=KUBECONFIG_PATH.read_text(encoding="utf-8") if KUBECONFIG_PATH.exists() else "",
        endpoint_exists=ENDPOINT_PATH.exists(),
        endpoint_text=ENDPOINT_PATH.read_text(encoding="utf-8") if ENDPOINT_PATH.exists() else "",
    )


def restore_local_access(snapshot: LocalAccessSnapshot) -> None:
    K8S_CONFIGURE_DIR.mkdir(parents=True, exist_ok=True)

    if snapshot.kubeconfig_exists:
        KUBECONFIG_PATH.write_text(snapshot.kubeconfig_text, encoding="utf-8")
    else:
        KUBECONFIG_PATH.unlink(missing_ok=True)

    if snapshot.endpoint_exists:
        ENDPOINT_PATH.write_text(snapshot.endpoint_text, encoding="utf-8")
    else:
        ENDPOINT_PATH.unlink(missing_ok=True)


def write_aggregate(
    artifact_dir: Path,
    *,
    game: str,
    selected_tasks: list[str],
    completed: list[TaskResult],
    pending: list[str],
) -> None:
    payload = {
        "game": game,
        "artifact_dir": str(artifact_dir),
        "selected_tasks": selected_tasks,
        "completed_tasks": [asdict(item) for item in completed],
        "pending_tasks": pending,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_json(artifact_dir / "aggregate-summary.json", payload)


def build_minikube_start_command(args: argparse.Namespace, profile: str) -> list[str]:
    command = [
        "minikube",
        "start",
        "-p",
        profile,
        "--driver",
        args.driver,
        "--listen-address",
        args.listen_address,
        "--apiserver-names",
        args.apiserver_name,
        "--ports",
        args.publish_port,
        "--cpus",
        str(args.cpus),
        "--memory",
        str(args.memory),
        "--wait=all",
        f"--wait-timeout={args.start_timeout}s",
    ]
    if args.kubernetes_version:
        command.extend(["--kubernetes-version", args.kubernetes_version])
    return command


def build_minikube_delete_command(profile: str) -> list[str]:
    return ["minikube", "delete", "-p", profile]


def run_task(args: argparse.Namespace, game: str, task: str, artifact_dir: Path, pytest_cmd: list[str]) -> TaskResult:
    task_dir = TESTS_ROOT / game / task
    profile = profile_name(args.profile_prefix, game, task)
    task_stub = f"{game}-{task}"
    log_file = artifact_dir / f"{task_stub}.log"
    summary_file = artifact_dir / f"{task_stub}-summary.json"
    failed_file = artifact_dir / f"{task_stub}-failures.txt"
    kept_profile = False

    if summary_file.exists() and not args.rerun:
        data = json.loads(summary_file.read_text(encoding="utf-8"))
        return TaskResult(**data)

    start_time = time.time()
    env = os.environ.copy()
    if args.skip_answer:
        env["SKIP_ANSWER_TESTS"] = "True"

    log_file.write_text(f"# Fresh Minikube task run\n# task={task}\n# profile={profile}\n", encoding="utf-8")
    exit_code = 1
    try:
        clear_python_cache(task_dir, log_file, "clear task python cache")
        run_command(
            build_minikube_delete_command(profile),
            log_file=log_file,
            title="minikube delete before start",
            check=False,
            timeout=args.delete_timeout,
        )
        run_command(
            build_minikube_start_command(args, profile),
            log_file=log_file,
            title="minikube start",
            timeout=args.start_timeout,
        )
        run_command(
            ["minikube", "-p", profile, "kubectl", "--", "get", "nodes", "-o", "wide"],
            log_file=log_file,
            title="cluster preflight",
        )
        write_local_kube_access(profile, log_file)
        pytest_command = pytest_cmd + ["--import-mode=importlib", "--rootdir=.", str(task_dir)]
        result = run_command(
            pytest_command,
            log_file=log_file,
            title="pytest task",
            env=env,
            cwd=REPO_ROOT,
            check=False,
        )
        exit_code = result.returncode
    except Exception as exc:  # noqa: BLE001
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"\nUNHANDLED_ERROR={exc}\n")
        exit_code = 1
    finally:
        if exit_code != 0 and args.keep_on_fail:
            kept_profile = True
        else:
            with log_file.open("a", encoding="utf-8") as handle:
                handle.write("\n## minikube delete\n")
                handle.write("COMMAND: minikube delete -p " + profile + "\n\n")
                subprocess.run(
                    build_minikube_delete_command(profile),
                    cwd=str(REPO_ROOT),
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False,
                    timeout=args.delete_timeout,
                )

    duration = round(time.time() - start_time, 2)
    log_text = log_file.read_text(encoding="utf-8", errors="replace")
    counts = parse_counts(log_text)
    failed_tests = parse_failed_tests(log_text)
    failed_file.write_text("\n".join(failed_tests) + ("\n" if failed_tests else ""), encoding="utf-8")
    payload = TaskResult(
        game=game,
        task=task,
        profile=profile,
        exit_code=exit_code,
        duration_seconds=duration,
        counts=counts,
        failed_tests=failed_tests,
        failed_phases=parse_failed_phases(failed_tests),
        signals=detect_signals(log_text),
        log_file=str(log_file),
        summary_file=str(summary_file),
        kept_profile=kept_profile,
        task_path=str(task_dir),
    )
    write_json(summary_file, asdict(payload))
    return payload


def main() -> int:
    args = parse_args()
    pytest_cmd = resolve_pytest_for_manifest(args.pytest_exe) if args.dry_run else resolve_pytest_executable(args.pytest_exe)
    if not args.dry_run:
        ensure_command("minikube")
        ensure_command("kubectl")
    tasks = apply_task_filters(discover_tasks(args.game), args)
    artifact_dir = artifact_dir_from_args(args.artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "game": args.game,
        "tasks": tasks,
        "artifact_dir": str(artifact_dir),
        "profile_prefix": args.profile_prefix,
        "driver": args.driver,
        "cpus": args.cpus,
        "memory": args.memory,
        "kubernetes_version": args.kubernetes_version,
        "delete_timeout": args.delete_timeout,
        "start_timeout": args.start_timeout,
        "listen_address": args.listen_address,
        "apiserver_name": args.apiserver_name,
        "publish_port": args.publish_port,
        "keep_on_fail": args.keep_on_fail,
        "skip_answer": args.skip_answer,
        "pytest_command_prefix": pytest_cmd,
        "dry_run": args.dry_run,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    write_json(artifact_dir / "run-manifest.json", manifest)

    if args.dry_run:
        print(json.dumps(manifest, indent=2))
        return 0

    local_access_snapshot = snapshot_local_access()
    preflight_log = artifact_dir / "run-preflight.log"
    preflight_log.write_text("# Fresh Minikube run preflight\n", encoding="utf-8")
    try:
        clear_python_cache(TESTS_ROOT, preflight_log, "clear all test python cache")
        completed: list[TaskResult] = []
        pending = list(tasks)
        write_aggregate(artifact_dir, game=args.game, selected_tasks=tasks, completed=completed, pending=pending)

        for task in tasks:
            result = run_task(args, args.game, task, artifact_dir, pytest_cmd)
            completed.append(result)
            pending = [item for item in pending if item != task]
            write_aggregate(artifact_dir, game=args.game, selected_tasks=tasks, completed=completed, pending=pending)
            print(
                json.dumps(
                    {
                        "task": task,
                        "profile": result.profile,
                        "exit_code": result.exit_code,
                        "duration_seconds": result.duration_seconds,
                        "counts": result.counts,
                        "failed_phases": result.failed_phases,
                        "signals": result.signals,
                        "kept_profile": result.kept_profile,
                    }
                ),
                flush=True,
            )
            if result.kept_profile:
                print(
                    f"Stopped after failing task {task} because --keep-on-fail preserved profile {result.profile}.",
                    flush=True,
                )
                return result.exit_code

        failures = [item for item in completed if item.exit_code != 0]
        return 1 if failures else 0
    finally:
        restore_local_access(local_access_snapshot)


if __name__ == "__main__":
    raise SystemExit(main())
