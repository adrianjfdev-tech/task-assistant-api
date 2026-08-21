from app.services.llm_service import parse_task
from app.repository.task_repository import tasks

def test_create_task_with_function_call():
    tasks.clear()

    result = parse_task(
        request="Submit the project report by Friday and mark it as high priority.",
        reference_date="2026-08-20",
        timezone="Asia/Kolkata",
    )

    assert result.status == "accepted"
    assert result.task is not None

    assert len(tasks) == 1

    created_task = tasks[0]

    assert created_task["id"] == 1
    assert created_task["title"]
    assert created_task["priority"] == "high"
    assert created_task["due_date"] == "2026-08-21"
