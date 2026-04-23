async def wait_all(
    iterable: Iterable[Coroutine], timeout: int = GENERAL_TIMEOUT
) -> list:
    """Shorthand for waiting for all the coroutines in the iterable given in parallel. Creates
    a task for each coroutine.
    Returns a list of results in the original order. If any single task raised an exception, this is raised.
    If multiple tasks raised exceptions, an AsyncException is raised containing all exceptions.
    """
    tasks = [asyncio.create_task(c) for c in iterable]
    if not tasks:
        return []
    _, pending = await asyncio.wait(tasks, timeout=timeout)
    if pending:
        for task in pending:
            task.cancel()
        raise asyncio.TimeoutError()
    results = []
    errors = []
    for task in tasks:
        try:
            results.append(task.result())
        except Exception as e:
            errors.append(e)
    if errors:
        if len(errors) == 1:
            raise errors[0]
        raise AsyncException(errors)
    return [task.result() for task in tasks]