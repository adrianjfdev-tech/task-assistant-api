# Task Assistant API — Architecture

## 1. High-Level Flow

```text
User
 │
 │ POST /tasks
 ▼
routes.py
 │
 │ TaskRequest
 ▼
parse_task()
 │
 │ receives LLMService
 ▼
LLMService
 │
 ├── GroqService
 ├── GeminiService
 └── other providers
 │
 ▼
LLM Provider
 │
 │ understands natural-language request
 │ decides: accept / reject
 │ extracts task fields
 ▼
LLM Result
 │
 ▼
parse_task()
 │
 ├── rejected → return rejection
 │
 └── accepted → create_task()
                         │
                         ▼
                  task_repository.py
                         │
                         ▼
                       Task
```

## 2. Main Files

### `app/main.py`

Creates and configures the FastAPI application.

```text
main.py
   │
   └── registers routes
```

It is the entry point of the API.

---

### `app/schemas.py`

Defines the structure of API requests and responses using Pydantic.

For example:

```text
POST /tasks
      │
      ▼
TaskRequest
```

It ensures that the data entering the API has the expected structure.

---

### `app/routes.py`

Defines the API endpoints.

For `POST /tasks`, it:

1. Receives the `TaskRequest`.
2. Creates the selected LLM provider.
3. Passes the request to `parse_task()`.
4. Handles accepted/rejected results.
5. Returns the created task.

```text
HTTP Request
     │
     ▼
routes.py
     │
     ▼
parse_task()
```

The route does not contain the actual LLM-prompting logic.

---

## 3. Task Parsing

### `app/services/llm_service.py`

This contains the provider-independent task-processing logic.

Its job is to:

1. Send the user's request to the selected LLM service.
2. Interpret the LLM result.
3. Determine whether the LLM called `create_task`.
4. Handle rejected requests.
5. Validate the structured result.
6. Create the task when accepted.

The important point is that this file does **not** need to know whether the provider is Groq or Gemini.

```text
parse_task()
     │
     │ uses
     ▼
LLMService
```

---

## 4. LLM Abstraction

### `app/services/providers/base.py`

Defines the common interface that every LLM provider must implement.

```python
class LLMService(ABC):

    @abstractmethod
    async def generate_task(
        self,
        request,
        reference_date,
        timezone,
    ):
        pass
```

This means:

> Every LLM provider must provide a `generate_task()` method with this interface.

It does not contain provider-specific code.

---

## 5. Groq Provider

### `app/services/providers/groq_service.py`

Contains the Groq-specific implementation.

It:

1. Gets `GROQ_API_KEY`.
2. Creates the Groq client.
3. Sends the system prompt and user request to Groq.
4. Provides the `create_task` tool.
5. Converts the Groq response into an `LLMResult`.

```text
GroqService
     │
     ▼
Groq API
     │
     ▼
LLMResult
```

The rest of the application does not need to know how Groq's API works.

---

## 6. LLM Result

### `app/services/llm_result.py`

Provides a common representation of an LLM response.

Conceptually:

```text
LLMResult
 ├── tool_name
 ├── tool_arguments
 └── content
```

For an accepted task:

```text
tool_name
    = "create_task"

tool_arguments
    = {
        title: "...",
        priority: "...",
        due_date: "..."
    }

content
    = None
```

For a rejected request:

```text
tool_name
    = None

tool_arguments
    = None

content
    = rejection JSON
```

This gives `llm_service.py` a provider-independent result to work with.

---

## 7. Task Prompt

### `app/services/task_prompt.py`

Contains the LLM instructions and tool definition.

The `SYSTEM_PROMPT` tells the LLM:

* What constitutes a valid task.
* When to accept or reject.
* How to determine priority.
* How to resolve relative dates.
* How to handle missing date context.
* How to handle ambiguous requests.
* What fields belong in the task.
* When to call `create_task`.

The prompt is the **decision-making instruction given to the LLM**.

---

## 8. Tool Calling

The LLM does not directly write to the repository.

Instead, it can call:

```text
create_task(
    title,
    priority,
    due_date
)
```

The LLM produces the arguments.

Python then uses those arguments:

```text
LLM
 │
 │ create_task(title, priority, due_date)
 ▼
Python
 │
 ▼
task_repository.py
```

Therefore:

> The LLM decides what structured task should be created. Python actually creates it.

---

## 9. Repository

### `app/repository/task_repository.py`

Responsible for storing tasks.

The LLM does not interact directly with the repository.

```text
LLM
 │
 ▼
structured arguments
 │
 ▼
llm_service.py
 │
 ▼
create_task()
 │
 ▼
task_repository.py
```

---

## 10. Provider Switching

The abstraction allows the provider to be changed without rewriting the task-parsing logic.

Current setup:

```text
routes.py
    │
    ▼
GroqService
    │
    ▼
Groq
```

Possible future setup:

```text
routes.py
    │
    ▼
GeminiService
    │
    ▼
Gemini
```

Both implement:

```python
LLMService.generate_task(...)
```

Therefore `parse_task()` can work with either provider.

The key idea is:

```text
                 LLMService
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
    GroqService           GeminiService
          │                     │
          ▼                     ▼
        Groq                  Gemini
```

The application depends on the **interface**, not directly on a specific LLM provider.

---

## 11. Complete Request Flow

Example request:

```text
"Urgent: finish my presentation by Friday"
```

with:

```text
reference_date = 2026-08-20
timezone = Asia/Kolkata
```

Flow:

```text
1. User
   │
   ▼
2. POST /tasks
   │
   ▼
3. routes.py
   │
   ▼
4. TaskRequest
   │
   ▼
5. parse_task()
   │
   ▼
6. GroqService.generate_task()
   │
   ▼
7. Groq API
   │
   │ SYSTEM_PROMPT
   │ +
   │ user request
   │ +
   │ date context
   │
   ▼
8. LLM interprets request
   │
   ▼
9. LLM calls create_task
   │
   │ title = "Finish my presentation"
   │ priority = "high"
   │ due_date = "2026-08-21"
   │
   ▼
10. GroqService converts response
    │
    ▼
11. LLMResult
    │
    ▼
12. parse_task()
    │
    ▼
13. create_task()
    │
    ▼
14. task_repository.py
    │
    ▼
15. Created task
    │
    ▼
16. routes.py
    │
    ▼
17. HTTP response
```

## 12. Core Responsibility Split

```text
main.py
   → Application setup

schemas.py
   → API data structure

routes.py
   → HTTP/API coordination

llm_service.py
   → Task-parsing logic

base.py
   → LLM provider contract

groq_service.py
   → Groq-specific implementation

gemini_service.py
   → Gemini-specific implementation

task_prompt.py
   → LLM instructions + tool definition

llm_result.py
   → Common LLM response format

task_repository.py
   → Task storage
```

### Core principle

The architecture separates **what the application wants from an LLM** from **how a particular provider performs it**.

```text
Application logic
       │
       ▼
  LLMService
       │
       ├── Groq
       ├── Gemini
       └── Future providers
```

This makes the LLM provider replaceable without changing the FastAPI/business-logic layer.
