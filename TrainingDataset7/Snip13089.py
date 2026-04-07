def task(
    function=None,
    *,
    priority=DEFAULT_TASK_PRIORITY,
    queue_name=DEFAULT_TASK_QUEUE_NAME,
    backend=DEFAULT_TASK_BACKEND_ALIAS,
    takes_context=False,
):
    from . import task_backends

    def wrapper(f):
        return task_backends[backend].task_class(
            priority=priority,
            func=f,
            queue_name=queue_name,
            backend=backend,
            takes_context=takes_context,
            run_after=None,
        )

    if function:
        return wrapper(function)
    return wrapper