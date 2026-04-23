def reuse_prev_task_chunks(task: dict, prev_tasks: list[dict], chunking_config: dict):
    """Attempt to reuse chunks from previous tasks for optimization.

    This function checks if chunks from previously completed tasks can be reused for
    the current task, which can significantly improve processing efficiency. It matches
    tasks based on page ranges and configuration digests.

    Args:
        task (dict): Current task dictionary to potentially reuse chunks for.
        prev_tasks (list[dict]): List of previous task dictionaries to check for reuse.
        chunking_config (dict): Configuration dictionary for chunk processing.

    Returns:
        int: Number of chunks successfully reused. Returns 0 if no chunks could be reused.

    Note:
        Chunks can only be reused if:
        - A previous task exists with matching page range and configuration digest
        - The previous task was completed successfully (progress = 1.0)
        - The previous task has valid chunk IDs
    """
    idx = 0
    while idx < len(prev_tasks):
        prev_task = prev_tasks[idx]
        if prev_task.get("from_page", 0) == task.get("from_page", 0) \
                and prev_task.get("digest", 0) == task.get("digest", ""):
            break
        idx += 1

    if idx >= len(prev_tasks):
        return 0
    prev_task = prev_tasks[idx]
    if prev_task["progress"] < 1.0 or not prev_task["chunk_ids"]:
        return 0
    task["chunk_ids"] = prev_task["chunk_ids"]
    task["progress"] = 1.0
    if "from_page" in task and "to_page" in task and int(task['to_page']) - int(task['from_page']) >= 10 ** 6:
        task["progress_msg"] = f"Page({task['from_page']}~{task['to_page']}): "
    else:
        task["progress_msg"] = ""
    task["progress_msg"] = " ".join(
        [datetime.now().strftime("%H:%M:%S"), task["progress_msg"], "Reused previous task's chunks."])
    prev_task["chunk_ids"] = ""

    return len(task["chunk_ids"].split())