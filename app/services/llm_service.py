import json

from pydantic import BaseModel, ValidationError
from typing import Literal

from app.repository.task_repository import create_task


class TaskResult(BaseModel):
    title: str
    description: str | None
    priority: Literal["low", "medium", "high"]
    due_date: str | None


class TaskParseResult(BaseModel):
    status: Literal["accepted", "rejected"]
    task: TaskResult | None
    reason: str | None


async def parse_task(
    request: str,
    reference_date: str | None = None,
    timezone: str | None = None,
    llm_service=None,
) -> TaskParseResult:

    if llm_service is None:
        raise RuntimeError("LLM service is not configured")

    response = await llm_service.generate_task(
        request=request,
        reference_date=reference_date,
        timezone=timezone,
    )

    # Rejected request: model did not call create_task.
    if response.tool_name is None:

        if not response.content:
            raise RuntimeError("LLM returned no content")

        try:
            return TaskParseResult.model_validate(
                json.loads(response.content)
            )
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(
                "LLM returned invalid structured output"
            ) from exc

    # Accepted request: model called create_task.
    if response.tool_name != "create_task":
        raise RuntimeError(
            f"LLM called unexpected tool: {response.tool_name}"
        )

    arguments = response.tool_arguments

    task = create_task(
        title=arguments["title"],
        priority=arguments["priority"],
        due_date=arguments["due_date"],
    )

    return TaskParseResult(
        status="accepted",
        task=TaskResult(
            title=task["title"],
            description=task["title"],
            priority=task["priority"],
            due_date=task["due_date"],
        ),
        reason=None,
    )