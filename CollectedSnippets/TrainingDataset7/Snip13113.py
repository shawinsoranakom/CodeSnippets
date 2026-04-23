def log_task_started(sender, task_result, **kwargs):
    logger.info(
        "Task id=%s path=%s state=%s",
        task_result.id,
        task_result.task.module_path,
        task_result.status,
    )