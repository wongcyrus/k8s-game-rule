# K8s Game Tools

Utilities for managing K8s game tasks and manifests.

## generate_manifests.py

Automatically generate `manifest.json` files for tasks by discovering test files.

### Features

- 🔍 **Auto-discovery**: Scans task directories for test files
- 📝 **Smart defaults**: Generates sensible configuration based on task structure
- 🎯 **Metadata extraction**: Extracts descriptions from instruction.md
- ⚙️ **Customizable**: Edit generated manifests to fine-tune configuration
- 🔒 **Safe**: Won't overwrite existing manifests without --overwrite flag

### Usage

```bash
# Generate manifests for all tasks in game01
python tools/generate_manifests.py game01

# Generate manifest for specific task
python tools/generate_manifests.py game01 --task 01_default_namespace

# Overwrite existing manifests
python tools/generate_manifests.py game01 --overwrite

# Dry run (preview without writing)
python tools/generate_manifests.py game01 --dry-run
```

### What It Generates

For a task with these test files:
```
01_default_namespace/
├── test_01_setup.py
├── test_05_check.py
└── test_06_cleanup.py
```

Generates:
```json
{
  "task_id": "01_default_namespace",
  "title": "01 Default Namespace",
  "description": "Learn 01 Default Namespace",
  "difficulty": "beginner",
  "estimated_minutes": 15,
  "phases": [
    {
      "id": "setup",
      "name": "Setup",
      "test_file": "test_01_setup.py",
      "points": 0,
      "timeout_seconds": 30,
      "max_attempts": 3
    },
    {
      "id": "check",
      "name": "Check",
      "test_file": "test_05_check.py",
      "points": 20,
      "timeout_seconds": 30,
      "max_attempts": 3
    },
    {
      "id": "cleanup",
      "name": "Cleanup",
      "test_file": "test_06_cleanup.py",
      "points": 0,
      "auto_run": true,
      "timeout_seconds": 30,
      "max_attempts": 1
    }
  ],
  "prerequisites": [],
  "tags": ["kubernetes", "kubectl"],
  "hints": [
    "Read the instruction carefully",
    "Use kubectl commands to complete the task",
    "Check the test results for detailed feedback"
  ]
}
```

### Phase Configuration

| Test File | Phase ID | Points | Timeout | Max Attempts | Auto-run |
|-----------|----------|--------|---------|--------------|----------|
| test_01_setup.py | setup | 0 | 30s | 3 | No |
| test_02_ready.py | ready | 5 | 30s | 3 | No |
| test_03_answer.py | answer | 10 | 30s | 3 | No |
| test_04_challenge.py | challenge | 15 | 60s | 5 | No |
| test_05_check.py | check | 20 | 30s | 3 | No |
| test_06_cleanup.py | cleanup | 0 | 30s | 1 | Yes |

### Difficulty Levels

Automatically determined by task number:
- Tasks 01-10: **beginner**
- Tasks 11-20: **intermediate**
- Tasks 21+: **advanced**

### Customization

After generation, you can edit the manifest.json to:
- Adjust timeouts for slow operations
- Change points distribution
- Add better descriptions
- Set prerequisites
- Add custom hints
- Change difficulty level

### Example Workflow

```bash
# 1. Generate manifests for all tasks
python tools/generate_manifests.py game01

# 2. Review generated manifests
ls tests/game01/*/manifest.json

# 3. Customize important tasks
vim tests/game01/05_important_task/manifest.json

# 4. Regenerate specific task if needed
python tools/generate_manifests.py game01 --task 05_important_task --overwrite
```

### Benefits

✅ **No manual JSON writing** - Generates from existing structure
✅ **Consistent format** - All manifests follow same schema
✅ **Quick start** - Generate all manifests in seconds
✅ **Incremental enhancement** - Generate defaults, customize later
✅ **Safe operation** - Won't overwrite without explicit flag

### Requirements

- Python 3.6+
- No external dependencies (uses only stdlib)

### Notes

- Skips tasks starting with `_` or containing `99_test_template`
- Extracts description from first non-empty line of instruction.md
- Calculates estimated time as 5 minutes per phase
- Generated manifests are valid and ready to use
- You can always edit generated manifests to fine-tune configuration
