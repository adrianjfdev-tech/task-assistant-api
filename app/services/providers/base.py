from abc import ABC, abstractmethod


class LLMService(ABC):

    @abstractmethod
    async def generate_task(
        self,
        request: str,
        reference_date: str | None,
        timezone: str | None,
    ):
        pass