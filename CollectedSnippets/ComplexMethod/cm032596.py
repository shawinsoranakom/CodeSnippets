def _find_task(data, task_id):
    if isinstance(data, dict):
        if data.get("id") == task_id:
            return data
        tasks = data.get("tasks")
        if isinstance(tasks, list):
            for item in tasks:
                if isinstance(item, dict) and item.get("id") == task_id:
                    return item
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("id") == task_id:
                return item
    return None