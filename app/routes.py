from fastapi import APIRouter, HTTPException

from app.schemas import TaskRequest
from app.services.llm_service import parse_task
from app.services.providers.groq_service import GroqService
from app.repository.task_repository import tasks


router = APIRouter()


@router.post("/tasks")
async def create_task(request: TaskRequest):

    llm_service = GroqService()

    result = await parse_task(
        request=request.request,
        reference_date=request.reference_date,
        timezone=request.timezone,
        llm_service=llm_service,
    )

    if result.status == "rejected":
        raise HTTPException(
            status_code=400,
            detail=result.reason,
        )

    if result.task is None:
        raise HTTPException(
            status_code=400,
            detail="Task could not be created",
        )

    return tasks[-1]