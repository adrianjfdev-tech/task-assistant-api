from dataclasses import dataclass


@dataclass
class LLMResult:
    tool_name: str | None
    tool_arguments: dict | None
    content: str | None