import os
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel


SYSTEM_PROMPT = """
You convert one natural-language request into one AI Task Assistant task.

Use only facts directly stated or unambiguously implied by the request
and the supplied date context. Do not invent people, deadlines, priorities,
descriptions, reminder schedules, notifications, recurrence, labels, or
extra tasks.

Inputs:
- request: the user's natural-language request
- reference_date: ISO date (YYYY-MM-DD), or null
- timezone: IANA timezone, or null

Return a task only when the request contains one meaningful, actionable task.
Reject requests that are ambiguous, speculative, informational, non-actionable,
contradictory, or contain multiple independent tasks.

For an accepted task:
- title: concise action-focused title. Remove conversational wrapper text
  such as "remind me to".
- description: preserve the core task wording without adding information.
  Use null only if no useful description can be safely produced.
- priority:
  - high only when explicitly indicated, such as "urgent", "high priority",
    or "critical".
  - low only when explicitly indicated.
  - medium otherwise.
- due_date:
  - Return YYYY-MM-DD or null only.
  - Resolve relative dates only using both reference_date and timezone.
  - "today" = reference_date.
  - "tomorrow" = one calendar day after reference_date.
  - "next <weekday>" = the first named weekday strictly after reference_date.
  - a bare weekday such as "Friday" = the named weekday on or after
    reference_date.
  - If the request has no reliable date, or relative-date context is
    incomplete or invalid, use null.
  - If a resolved due date is before reference_date, reject the request.
  - Do not create a time, reminder, or notification. A time mentioned by
    the user may remain only in description.

Return only the structured output.
"""


class TaskResult(BaseModel):
    title: str
    description: str | None
    priority: Literal["low", "medium", "high"]
    due_date: str | None


class TaskParseResult(BaseModel):
    status: Literal["accepted", "rejected"]
    task: TaskResult | None
    reason: str | None


def parse_task(
    request: str,
    reference_date: str | None = None,
    timezone: str | None = None,
) -> TaskParseResult:

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    client = genai.Client(api_key=api_key)

    user_input = f"""
request: {request}
reference_date: {reference_date}
timezone: {timezone}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=TaskParseResult,
        ),
    )

    if response.parsed is None:
        raise RuntimeError("Gemini returned no structured result")

    return response.parsed