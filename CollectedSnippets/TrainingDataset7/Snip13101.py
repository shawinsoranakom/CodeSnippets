def wrapper(f):
        return task_backends[backend].task_class(
            priority=priority,
            func=f,
            queue_name=queue_name,
            backend=backend,
            takes_context=takes_context,
            run_after=None,
        )