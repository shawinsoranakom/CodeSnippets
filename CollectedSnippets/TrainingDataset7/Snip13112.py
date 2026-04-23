def log_task_enqueued(sender, task_result, **kwargs):
    logger.debug(
        "Task id=%s path=%s enqueued backend=%s",
        task_result.id,
        task_result.task.module_path,
        task_result.backend,
    )