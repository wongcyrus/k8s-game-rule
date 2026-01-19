# Kubernetes Isekai - Project Design & Architecture Documentation

## 🎯 Project Overview

**Kubernetes Isekai (異世界)** is a gamified learning platform for Kubernetes education, designed for students at Hong Kong Institute of Information Technology (HKIIT). It transforms Kubernetes learning into an RPG-style adventure where students complete tasks to learn K8s concepts hands-on.

### Key Features
- **Gamified Learning**: RPG-style task progression with NPC interactions
- **Automated Testing**: Pytest-based validation of student solutions
- **Cloud Integration**: AWS Lambda for scalable grading, DynamoDB for session management
- **Free Access**: Uses AWS Academy Learner Lab with Minikube/Kubernetes
- **GenAI Integration**: Dynamic NPC interactions for enhanced engagement

---

## 🏗️ Architecture Design

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Student Interface                         │
│              (Game UI + K8s Cluster Access)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Task Definition Layer                       │
│         (This Repository - Test Definitions)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Setup      │→ │   Answer     │→ │    Check     │→     │
│  │  (test_01)   │  │  (test_03)   │  │  (test_05)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Validation & Grading Layer                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │  AWS Lambda (Pytest Execution)                     │     │
│  │  - Runs test suites                                │     │
│  │  - Validates student solutions                     │     │
│  │  - Returns results                                 │     │
│  └────────────────────────────────────────────────────┘     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Data Persistence Layer                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │  AWS DynamoDB                                      │     │
│  │  - Session data (student progress)                 │     │
│  │  - Task parameters (randomized values)             │     │
│  │  - K8s credentials                                 │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

### Directory Layout

```
k8s-game-rule/
├── tests/
│   ├── game01/                          # Game 1 - Basic K8s Tasks
│   │   ├── 01_default_namespace/        # Task 1: Default namespace check
│   │   ├── 02_create_namespace/         # Task 2: Create namespace
│   │   ├── 03_create_pod_port_80/       # Task 3: Create pod with port
│   │   ├── 13_pod_names_nginx1_with_label/  # Labels
│   │   ├── 14_change_pod_label/         # Modify labels
│   │   ├── 15_add_new_label_tier/       # Add labels
│   │   ├── 16_annotation_owner_marketing/   # Annotations
│   │   ├── 24_create_a_configmap/       # ConfigMaps
│   │   ├── 28_configMap_to_pod_volume_mount/  # Volume mounts
│   │   ├── 29_nginx_pod_user_id/        # Security contexts
│   │   ├── 31_limit_range/              # Resource limits
│   │   ├── 36_secret/                   # Secrets
│   │   └── 99_test_template/            # Template for new tasks
│   │
│   ├── helper/                          # Utility modules
│   │   ├── k8s_client_helper.py        # K8s Python client wrapper
│   │   ├── kubectrl_helper.py          # kubectl command wrapper
│   │   └── test_helper.py              # Test deployment helpers
│   │
│   └── conftest.py                      # Pytest configuration & fixtures
│
├── k8s-configure/                       # K8s cluster configuration
│   ├── endpoint.txt                     # K8s API endpoint
│   ├── client.crt                       # Client certificate (gitignored)
│   └── client.key                       # Client key (gitignored)
│
├── .env                                 # Environment configuration
├── requirements.txt                     # Python dependencies
├── pytest.ini                           # Pytest settings
└── README.md                            # Project documentation
```

---

## 🔄 Task Lifecycle & Test Flow

### Standard Test Sequence

Each task follows a standardized 6-phase lifecycle:

```
test_01_setup.py    →  test_02_ready.py   →  test_03_answer.py  →
test_04_challenge.py →  test_05_check.py   →  test_06_cleanup.py
```

#### Phase Breakdown

| Phase | File | Purpose | Execution Context |
|-------|------|---------|-------------------|
| **1. Setup** | `test_01_setup.py` | Prepare environment, create prerequisites (namespaces, base resources) | Always runs |
| **2. Ready** | `test_02_ready.py` | Verify environment is ready for student work | Optional |
| **3. Answer** | `test_03_answer.py` | Deploy the correct solution (for testing/validation) | Skippable via `SKIP_ANSWER_TESTS=True` |
| **4. Challenge** | `test_04_challenge.py` | Additional validation or complex checks | Optional |
| **5. Check** | `test_05_check.py` | **Core validation** - Verify student's solution meets requirements | Always runs |
| **6. Cleanup** | `test_06_cleanup.py` | Clean up resources (delete namespaces, pods, etc.) | Always runs |

### Execution Modes

#### Local Development Mode
```bash
# Run all tasks
pytest --import-mode=importlib --rootdir=.

# Run single task
pytest --import-mode=importlib --rootdir=. tests/game01/02_create_namespace/

# Skip answer tests (student mode)
SKIP_ANSWER_TESTS=True pytest --import-mode=importlib --rootdir=.
```

#### Production Mode (AWS Lambda)
- Tests run in Lambda with `/tmp/json_input.json` containing session data
- Results returned to grading API
- Session data fetched from DynamoDB

---

## 🧩 Core Components

### 1. Session Management (`conftest.py`)

**Purpose**: Centralized configuration and session data injection for all tests

**Key Functions**:

```python
@pytest.fixture(scope="module", autouse=True)
def json_input(request):
    """
    Provides test configuration from multiple sources:
    1. DynamoDB (production/game mode)
    2. Local session.json files (development)
    3. /tmp/json_input.json (Lambda execution)
    """
```

**Session Data Structure**:
```json
{
  "cert_file": "~/.minikube/profiles/minikube/client.crt",
  "key_file": "~/.minikube/profiles/minikube/client.key",
  "ca_file": "~/.minikube/ca.crt",
  "host": "https://192.168.49.2:8443",
  "namespace": "randomname123456789",
  "value1": "some_value",
  "value2": "another_value"
}
```

**Template Rendering with Jinja2**:
- Session values support Jinja2 templates
- Built-in functions: `random_name()`, `random_number()`, `student_id()`, `base64_encode()`
- Example: `"namespace": "{{random_name()}}{{student_id()}}"`

### 2. Kubernetes Helpers

#### `k8s_client_helper.py` - Python Client Wrapper

```python
def configure_k8s_client(json_input):
    """
    Configures Kubernetes Python client with certificates
    Returns: CoreV1Api instance for K8s operations
    """
```

**Usage Pattern**:
```python
k8s_client = configure_k8s_client(json_input)
namespaces = k8s_client.list_namespace()
pod = k8s_client.read_namespaced_pod(name="nginx", namespace="default")
```

#### `kubectrl_helper.py` - kubectl Command Wrapper

```python
def build_kube_config(client_certificate, client_key, endpoint, ca_certificate=None):
    """
    Generates kubeconfig YAML dynamically
    Returns: Encoded kubeconfig bytes
    """

def run_kubectl_command(kube_config, command):
    """
    Executes kubectl commands with temporary kubeconfig
    Returns: Command stdout/stderr
    """
```

**Usage Pattern**:
```python
kube_config = build_kube_config(cert, key, host, ca)
result = run_kubectl_command(kube_config, "kubectl get pods -n default")
```

#### `test_helper.py` - YAML Deployment Helper

```python
def deploy_answer(json_input):
    """
    Renders answer.template.yaml with session data
    Generates answer.gen.yaml
    Applies to K8s cluster
    """

def deploy_setup(json_input):
    """
    Same as deploy_answer but for setup.template.yaml
    """
```

### 3. Template System

**YAML Templates** use Jinja2 for dynamic resource generation:

```yaml
# answer.template.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: {{ namespace }}
---
apiVersion: v1
kind: Pod
metadata:
  name: nginx-pod
  labels:
    app: {{ app_label }}
  namespace: {{ namespace }}
spec:
  containers:
    - name: nginx
      image: nginx:{{ nginx_version }}
```

**Rendering Flow**:
1. Read `answer.template.yaml`
2. Inject values from `json_input` (session data)
3. Generate `answer.gen.yaml`
4. Apply to cluster: `kubectl apply -f answer.gen.yaml`

---

## 🎮 Task Design Patterns

### Pattern 1: Simple Resource Creation

**Example**: `02_create_namespace`

```
Setup: No prerequisites
Answer: Create namespace from template
Check: Verify namespace exists (Python client + kubectl)
Cleanup: Delete namespace
```

### Pattern 2: Resource Modification

**Example**: `14_change_pod_label`

```
Setup: Create namespace + pod with label app=v1
Answer: Update pod label to app=v2
Check: Verify label changed
Cleanup: Delete namespace (cascades to pod)
```

### Pattern 3: Complex Configuration

**Example**: `28_configMap_to_pod_volume_mount`

```
Setup: Create namespace
Answer: 
  - Create ConfigMap with key-value pairs
  - Create Pod with volume mount from ConfigMap
Check:
  - Verify ConfigMap data
  - Verify Pod volume configuration
  - Verify mount path
Cleanup: Delete namespace
```

### Pattern 4: Troubleshooting Tasks

**Example**: `34_failed_pod`

```
Setup: Create namespace with resource quotas
Answer: Attempt to create pod exceeding limits (expected to fail)
Check: Verify pod creation failed with correct error
Cleanup: Delete namespace
```

---

## 🔐 Security & Authentication

### Certificate-Based Authentication

**Local Development** (Minikube):
```json
{
  "cert_file": "~/.minikube/profiles/minikube/client.crt",
  "key_file": "~/.minikube/profiles/minikube/client.key",
  "ca_file": "~/.minikube/ca.crt",
  "host": "https://192.168.49.2:8443"
}
```

**Production** (DynamoDB):
```json
{
  "$client_certificate": "-----BEGIN CERTIFICATE-----\n...",
  "$client_key": "-----BEGIN RSA PRIVATE KEY-----\n...",
  "$endpoint": "https://k8s-api.example.com:6443"
}
```

### Credential Flow

1. **DynamoDB Storage**: Certificates stored per student/task
2. **Lambda Retrieval**: Fetched at test runtime
3. **Temporary Files**: Written to `/tmp` in Lambda
4. **Kubeconfig Generation**: Dynamic kubeconfig created per request
5. **Cleanup**: Automatic cleanup after test execution

---

## 📊 Data Model

### DynamoDB Schema

**Table**: `SessionTable`

**Primary Key**:
- Partition Key: `email` (student email)
- Sort Key: `game` (format: `game01#02_create_namespace`)

**Attributes**:
```json
{
  "email": "student@vtc.edu.hk",
  "game": "game01#02_create_namespace",
  "session": "{...}",  // JSON string with task parameters
  "timestamp": 1234567890,
  "status": "in_progress"
}
```

### Session JSON Structure

```json
{
  "$client_certificate": "...",
  "$client_key": "...",
  "$endpoint": "https://...",
  "namespace": "randomname123456789",
  "value1": "config_value_1",
  "value2": "config_value_2",
  "nginx_version": "1.21",
  "app_label": "frontend"
}
```

---

## 🧪 Testing Strategy

### kubectl-Based Validation Approach

All check tests use **kubectl commands** exclusively for validation:

**kubectl Commands** (subprocess)
- CLI-based validation
- JSON output parsing for structured data
- Simulates real-world student workflow
- Consistent with how students interact with Kubernetes
- Eliminates dependency on Python Kubernetes client library

**Example**:
```python
def test_001_namespace_exists_with_kubectl(self, json_input):
    kube_config = build_kube_config(
        json_input["cert_file"], json_input["key_file"], json_input["host"]
    )
    result = run_kubectl_command(kube_config, "kubectl get namespace")
    assert namespace in result, f"Namespace '{namespace}' does not exist"

def test_002_pod_details_with_kubectl(self, json_input):
    command = f"kubectl get pod {pod_name} -n {namespace} -o json"
    result = run_kubectl_command(kube_config, command)
    pod_data = json.loads(result)
    assert pod_data["metadata"]["name"] == pod_name
```

### Test Ordering

Pytest execution order controlled by:
1. **Filename sorting**: `test_01` → `test_02` → ... → `test_06`
2. **Directory sorting**: Tasks run in alphabetical order
3. **Custom sorting** in `conftest.py`:
```python
def pytest_collection_modifyitems(config, items):
    sorted_items.sort(
        key=lambda item: (os.path.dirname(item.path), os.path.basename(item.path))
    )
```

---

## 🚀 Deployment & Execution

### Local Development Setup

```bash
# 1. Create virtual environment
./create_virtural_env.sh

# 2. Configure K8s endpoint
echo "https://192.168.49.2:8443" > k8s-configure/endpoint.txt

# 3. Copy certificates (Minikube)
cp ~/.minikube/profiles/minikube/client.crt k8s-configure/
cp ~/.minikube/profiles/minikube/client.key k8s-configure/

# 4. Configure environment
cat > .env << EOF
SKIP_ANSWER_TESTS=True
SESSION_FROM_DYNAMODB=False
EOF

# 5. Run tests
pytest --import-mode=importlib --rootdir=.
```

### AWS Lambda Deployment

**Lambda Function**:
- Runtime: Python 3.x
- Handler: Custom pytest runner
- Timeout: 5 minutes
- Memory: 512MB
- Environment: `/tmp/json_input.json` with session data

**Execution Flow**:
1. API Gateway receives grading request
2. Lambda fetches session from DynamoDB
3. Writes session to `/tmp/json_input.json`
4. Executes pytest for specific task
5. Returns test results (pass/fail + logs)
6. Updates student progress in DynamoDB

---

## 🎓 Pedagogical Design

### Learning Progression

**Beginner Tasks** (01-10):
- Namespaces, Pods, Basic YAML
- Simple kubectl commands
- Resource inspection

**Intermediate Tasks** (11-25):
- Labels & Annotations
- ConfigMaps & Secrets
- Environment variables
- Volume mounts

**Advanced Tasks** (26-38):
- Security contexts
- Resource quotas & limits
- Troubleshooting
- Multi-resource configurations

### Randomization Strategy

**Why Randomize?**
- Prevents answer sharing
- Ensures understanding over memorization
- Simulates real-world variability

**What's Randomized?**
- Namespace names: `{{random_name()}}{{student_id()}}`
- Configuration values: `{{random_number(1,10)}}`
- Resource names (in some tasks)

---

## 🔧 Extension & Customization

### Adding New Tasks

**Step 1**: Copy template
```bash
cp -r tests/game01/99_test_template tests/game01/40_new_task
```

**Step 2**: Create instruction
```markdown
# instruction.md
Create a deployment with 3 replicas of nginx in namespace '{{namespace}}'.
```

**Step 3**: Define session variables
```json
// session.json
{
  "namespace": "{{random_name()}}{{student_id()}}",
  "replicas": "{{random_number(2,5)}}"
}
```

**Step 4**: Create templates
```yaml
# setup.template.yaml (if needed)
apiVersion: v1
kind: Namespace
metadata:
  name: {{namespace}}

# answer.template.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: {{namespace}}
spec:
  replicas: {{replicas}}
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:latest
```

**Step 5**: Implement tests
```python
# test_01_setup.py
from tests.helper.test_helper import deploy_setup

def test_setup(json_input):
    deploy_setup(json_input)

# test_03_answer.py
from tests.helper.test_helper import deploy_answer

def test_answer(json_input):
    deploy_answer(json_input)

# test_05_check.py
from tests.helper.k8s_client_helper import configure_k8s_client

class TestCheck:
    def test_001_deployment_exists(self, json_input):
        k8s_client = configure_k8s_client(json_input)
        apps_v1 = client.AppsV1Api()
        deployment = apps_v1.read_namespaced_deployment(
            name="nginx-deployment",
            namespace=json_input["namespace"]
        )
        assert deployment.spec.replicas == int(json_input["replicas"])

# test_06_cleanup.py
from tests.helper.kubectrl_helper import delete_namespace

def test_cleanup(json_input):
    delete_namespace(json_input)
```

---

## 🐛 Debugging & Troubleshooting

### Common Issues

**Issue 1**: Tests not running in order
```bash
# Clear Python cache
./clean_python_cache.sh
```

**Issue 2**: Certificate errors
```bash
# Verify certificates exist
ls -la k8s-configure/client.{crt,key}

# Test connection
kubectl --kubeconfig=<generated> get nodes
```

**Issue 3**: Session data not loading
```python
# Check conftest.py logs
pytest --log-cli-level=DEBUG
```

### Logging

**Pytest Configuration** (`pytest.ini`):
```ini
[pytest]
log_cli = 1
log_format = %(asctime)s %(levelname)s %(message)s
log_date_format = %Y-%m-%d %H:%M:%S
log_cli_level=INFO
```

**In Tests**:
```python
import logging

logging.info("Checking namespace: %s", namespace)
logging.debug("Full pod spec: %s", pod)
logging.error("Failed to create resource: %s", error)
```

---

## 📈 Future Enhancements

### Planned Features

1. **Multi-Cluster Support**: Test across different K8s distributions
2. **Real-Time Feedback**: WebSocket-based live validation
3. **Hint System**: Progressive hints for stuck students
4. **Leaderboard**: Gamification with points and rankings
5. **Custom Scenarios**: Student-created challenges
6. **CI/CD Integration**: Automated task validation on commit

### Scalability Considerations

- **Lambda Concurrency**: Handle 100+ simultaneous students
- **DynamoDB Capacity**: Auto-scaling for session storage
- **K8s Cluster**: Multi-tenant isolation with namespaces
- **Cost Optimization**: Spot instances for student clusters

---

## 👥 Development Team

**Core Developers** (HKIIT Students):
- 錢弘毅 (Hongyi Qian)
- Ho Chun Sun Don (何俊申)
- Kit Fong Loo
- Yuehan WU

**Program**: Higher Diploma in Cloud and Data Centre Administration

---

## 📚 Key Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Test framework & automation | 3.x |
| Pytest | Test execution engine | Latest |
| Kubernetes Python Client | K8s API interaction | Latest |
| kubectl | CLI-based validation | 1.x |
| Jinja2 | Template rendering | Latest |
| Boto3 | AWS SDK (DynamoDB, Lambda) | Latest |
| AWS Lambda | Serverless grading | N/A |
| AWS DynamoDB | Session storage | N/A |
| Minikube | Local K8s development | Latest |

---

## 🎯 Design Principles

1. **Separation of Concerns**: Setup → Answer → Check → Cleanup
2. **Idempotency**: Tests can run multiple times safely
3. **Isolation**: Each task uses unique namespaces
4. **Dual Validation**: Python client + kubectl for robustness
5. **Template-Driven**: YAML templates for consistency
6. **Randomization**: Prevent answer sharing
7. **Scalability**: Serverless architecture for cost efficiency
8. **Observability**: Comprehensive logging at all levels

---

## 📝 Conclusion

This project demonstrates a sophisticated approach to automated Kubernetes education, combining:
- **Gamification** for engagement
- **Automation** for scalability
- **Cloud-native** architecture for cost efficiency
- **Dual validation** for reliability
- **Template-driven** design for maintainability

The modular structure allows easy addition of new tasks while maintaining consistency across the learning experience.
