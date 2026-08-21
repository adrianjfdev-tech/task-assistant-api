from pydantic import BaseModel


class TaskRequest(BaseModel):
    request: str
    reference_date: str | None = None
    timezone: str | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    priority: str
    due_date: str | None