# AI Task Assistant API - Requirements

## 1. Problem statement

People frequently describe tasks in everyday language, including details such as a deadline, urgency, and notes. The system shall provide a REST API that uses a large language model (LLM) to interpret such requests and create structured task records that can be managed through standard CRUD operations.

For example, given: "Remind me to submit the project report by Friday and mark it as high priority," the API should produce a task equivalent to:

```json
{
  "title": "Submit project report",
  "description": "Submit the project report",
  "priority": "high",
  "due_date": "2026-08-21"
}
```

The resulting task must be available for retrieval, update, and deletion through the API.

## 2. Functional requirements

### FR-01: Create a task from natural language

The system shall accept a natural-language task request and use an LLM to convert it into a structured task object.

### FR-02: Extract task fields

The system shall extract or infer a concise `title`, an optional `description`, a `priority`, and an optional `due_date` from the request. Dates shall be returned in ISO 8601 calendar-date format (`YYYY-MM-DD`).

### FR-03: Apply defaults

When a request does not specify a priority, the system shall assign `medium`. When no due date can be determined, the system shall store `null` for `due_date`. The system shall not invent a due date that is not supported by the request.

### FR-04: Persist created tasks

The system shall assign each successfully created task a unique identifier and persist the structured task so that it remains available to later API requests.

### FR-05: Retrieve tasks

The system shall provide an endpoint that returns all stored tasks. The response shall include each task's identifier, title, description, priority, due date, creation timestamp, and update timestamp.

### FR-06: Retrieve a specific task

The system shall provide an endpoint that returns one task when given its identifier.

### FR-07: Update a task

The system shall provide an endpoint to update one or more editable fields of an existing task: `title`, `description`, `priority`, and `due_date`. Fields omitted from a partial update shall retain their current values.

### FR-08: Delete a task

The system shall provide an endpoint that permanently deletes a task when given its identifier and confirms successful deletion without returning the deleted task as an active resource.

### FR-09: Validate structured task data

The system shall validate all manually supplied or LLM-produced task fields before persistence. Accepted priority values are `low`, `medium`, and `high`.

### FR-10: Make date interpretation reproducible

For relative dates such as "Friday," the natural-language creation request shall include a reference date (or the API shall document the server's current date and timezone used). The response shall return the resolved date so the caller can verify the interpretation.

## 3. Non-functional requirements

### NFR-01: API consistency

The API shall use JSON request and response bodies, standard HTTP status codes, stable field names, and ISO 8601 timestamps in UTC for `created_at` and `updated_at`.

### NFR-02: Reliability and data integrity

The system shall not persist a task if LLM output is missing required data or fails validation. Failed requests shall leave existing tasks unchanged.

### NFR-03: Performance

For requests that do not require LLM processing (retrieve, update, and delete), the API should respond within 500 ms under normal local operating conditions. Natural-language task creation may take longer and shall enforce a configurable timeout for the LLM call.

### NFR-04: Security and configuration

LLM credentials and database connection settings shall be read from environment-based configuration and shall never be returned in API responses, logs, source control, or error messages.

### NFR-05: Maintainability and observability

The implementation shall separate HTTP handling, task persistence, and LLM parsing concerns. It shall log request failures with safe diagnostic context and support automated tests for validation and CRUD behavior.

## 4. User flow

1. A client sends a natural-language request to create a task, optionally including a reference date and timezone for relative-date resolution.
2. The API validates that the request is present and calls the LLM with a constrained structured-output schema.
3. The API validates and normalizes the LLM result, applies defaults, and stores the task.
4. The API returns the newly created task and its identifier.
5. The client retrieves the complete task list or a specific task as needed.
6. The client may update individual task fields using the task identifier.
7. The client may delete the task using the task identifier.

## 5. Expected inputs and outputs

### 5.1 Create from natural language

**Input** — `POST /tasks/from-natural-language`

```json
{
  "request": "Remind me to submit the project report by Friday and mark it as high priority.",
  "reference_date": "2026-08-20",
  "timezone": "Asia/Kolkata"
}
```

`request` is required. `reference_date` and `timezone` are optional unless the client needs deterministic interpretation of relative dates.

**Successful output** — `201 Created`

```json
{
  "id": "task_01J...",
  "title": "Submit project report",
  "description": "Submit the project report",
  "priority": "high",
  "due_date": "2026-08-21",
  "created_at": "2026-08-20T12:30:00Z",
  "updated_at": "2026-08-20T12:30:00Z"
}
```

### 5.2 Retrieve all tasks

**Input** — `GET /tasks`

**Successful output** — `200 OK`, containing a JSON array of task objects. An empty collection shall return `[]`.

### 5.3 Retrieve one task

**Input** — `GET /tasks/{task_id}`

**Successful output** — `200 OK`, containing the requested task object.

### 5.4 Update one task

**Input** — `PATCH /tasks/{task_id}`

```json
{
  "priority": "high",
  "due_date": "2026-08-25"
}
```

`title`, `description`, `priority`, and `due_date` are editable. `due_date` may be `null` to clear a deadline.

**Successful output** — `200 OK`, containing the complete updated task object.

### 5.5 Delete one task

**Input** — `DELETE /tasks/{task_id}`

**Successful output** — `204 No Content`.

## 6. Error and edge cases

1. **Empty request:** A missing, blank, or whitespace-only natural-language request shall return `400 Bad Request` and shall not call the LLM.
2. **Ambiguous or non-task request:** If the LLM cannot determine a meaningful task title, the API shall return `422 Unprocessable Entity` with a safe explanation and shall not persist a task.
3. **Invalid LLM output:** If the LLM response is malformed, violates the structured schema, or contains an unsupported priority, the API shall reject it with `422 Unprocessable Entity` and shall not persist a task.
4. **Invalid relative-date context:** If `reference_date` is malformed, `timezone` is invalid, or a relative date cannot be resolved reliably, the API shall return `400 Bad Request` or `422 Unprocessable Entity` and explain the affected field.
5. **Past deadline:** A due date resolved to the past shall be accepted only if the API documents that behaviour; the default behaviour shall be to return `422 Unprocessable Entity` so the client can clarify the task.
6. **Invalid update payload:** An update with no editable fields, an empty title, an unsupported priority, or an invalid date format shall return `400 Bad Request` or `422 Unprocessable Entity` without modifying the existing task.
7. **Unknown task identifier:** Retrieval, update, or deletion of a task that does not exist shall return `404 Not Found`.
8. **Duplicate deletion / concurrent modification:** Repeating a deletion after the task has been removed, or updating a task that was deleted concurrently, shall return `404 Not Found`.
9. **LLM unavailable or timed out:** If the LLM provider cannot be reached, rate-limits the request, or exceeds the configured timeout, the API shall return `503 Service Unavailable` (or `504 Gateway Timeout` for a timeout) and shall not create a partial task.
10. **Persistence failure:** If storage fails after parsing, the API shall return `500 Internal Server Error` and shall not report a task as created unless the record was successfully committed.

All error responses shall use a consistent JSON shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "priority must be one of: low, medium, high",
    "details": [{ "field": "priority", "issue": "unsupported value" }]
  }
}
```

## 7. Assumptions

- The initial release is single-user and does not require authentication, authorization, or tenant isolation.
- A configured LLM provider is available and can be instructed to return data matching the required task schema.
- Task titles are required and descriptions are optional.
- Priorities are limited to `low`, `medium`, and `high`; `medium` is the default.
- Due dates represent calendar dates rather than exact reminder times. Time-of-day reminders are not modeled in this release.
- The client supplies `reference_date` and `timezone` whenever a relative date must resolve deterministically; otherwise the server's documented current date and timezone are used.
- Tasks remain stored until explicitly deleted.

## 8. Out-of-scope functionality

- User accounts, authentication, authorization, and multi-user task ownership.
- Sending notifications, push alerts, emails, calendar events, or scheduled reminders.
- Recurring tasks, subtasks, task dependencies, labels, attachments, and comments.
- Natural-language updates to existing tasks; updates use structured API fields only.
- Full-text search, pagination, filtering, sorting, and bulk task operations.
- Collaborative sharing, assignment to other people, and audit-history/version restoration.
- Multilingual parsing guarantees, voice input, and client user-interface implementation.
