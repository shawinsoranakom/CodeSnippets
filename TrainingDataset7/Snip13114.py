def log_task_finished(sender, task_result, **kwargs):
    # Signal is sent inside exception handlers, so exc_info() is available.
    exc_info = sys.exc_info()
    logger.log(
        (
            logging.ERROR
            if task_result.status == TaskResultStatus.FAILED
            else logging.INFO
        ),
        "Task id=%s path=%s state=%s",
        task_result.id,
        task_result.task.module_path,
        task_result.status,
        exc_info=exc_info if exc_info[0] else None,
    )