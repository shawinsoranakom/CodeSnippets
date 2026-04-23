async def _run_parallel(*coros):
    """
    Execute multiple asynchronous coroutines in parallel,
    sharing the current context between them.
    """
    context = contextvars.copy_context()

    if len(coros) == 0:
        return []

    async def run(i, coro):
        results[i] = await coro

    try:
        async with asyncio.TaskGroup() as tg:
            results = [None] * len(coros)
            for i, coro in enumerate(coros):
                tg.create_task(run(i, coro), context=context)
        return results
    except BaseExceptionGroup as exception_group:
        if len(exception_group.exceptions) == 1:
            raise exception_group.exceptions[0]
        raise
    finally:
        _restore_context(context=context)