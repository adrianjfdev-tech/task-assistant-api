import os
import json
from dotenv import load_dotenv
from groq import AsyncGroq

from app.services.llm_result import LLMResult
from app.services.providers.base import LLMService
from app.services.task_prompt import SYSTEM_PROMPT, CREATE_TASK_TOOL

load_dotenv()


class GroqService(LLMService):

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

        self.client = AsyncGroq(api_key=api_key)

    async def generate_task(
        self,
        request: str,
        reference_date: str | None,
        timezone: str | None,
    ):
        user_input = f"""
request: {request}
reference_date: {reference_date}
timezone: {timezone}
"""

        response = await self.client.chat.completions.create(
            model="openai/gpt-oss-120b",
            tools=[CREATE_TASK_TOOL],
            tool_choice="auto",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_input,
                },
            ],
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return LLMResult(
                tool_name=None,
                tool_arguments=None,
                content=message.content,
            )

        tool_call = message.tool_calls[0]

        return LLMResult(
            tool_name=tool_call.function.name,
            tool_arguments=json.loads(tool_call.function.arguments),
            content=None,
        )