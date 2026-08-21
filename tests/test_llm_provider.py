import pytest

from app.services.providers.groq_service import GroqService


@pytest.mark.anyio
async def test_groq_service():
    service = GroqService()

    response = await service.generate_task(
        request="Submit the project report by Friday and mark it high priority.",
        reference_date="2026-08-20",
        timezone="Asia/Kolkata",
    )

    assert response is not None