from pathlib import Path

folders = [
    "app",
    "app/services",
    "app/repository",
    "tests",
    "spec",
    "evaluation",
    "docs",
]

files = [
    "app/__init__.py",
    "app/main.py",
    "app/models.py",
    "app/schemas.py",
    "app/routes.py",
    "app/services/__init__.py",
    "app/services/llm_service.py",
    "app/repository/__init__.py",
    "app/repository/task_repository.py",
    "tests/test_tasks.py",
    "tests/test_llm.py",
    "spec/requirements.md",
    "spec/api-spec.yaml",
    "evaluation/test_cases.json",
    "evaluation/evaluation.md",
    "docs/azure-mapping.md",
    "README.md",
    "requirements.txt",
]

for folder in folders:
    Path(folder).mkdir(parents=True, exist_ok=True)

for file in files:
    Path(file).touch(exist_ok=True)

print("Project structure created successfully!")