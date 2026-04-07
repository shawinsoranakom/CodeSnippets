def clear_tasks_handlers(*, setting, **kwargs):
    """Reset the connection handler whenever the settings change."""
    if setting == "TASKS":
        from . import task_backends

        task_backends._settings = task_backends.settings = (
            task_backends.configure_settings(None)
        )
        task_backends._connections = Local()