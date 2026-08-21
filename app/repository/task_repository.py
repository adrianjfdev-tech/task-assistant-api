tasks = []


def create_task(title, priority, due_date):
    task = {
        "id": len(tasks) + 1,
        "title": title,
        "priority": priority,
        "due_date": due_date,
    }

    tasks.append(task)

    return task