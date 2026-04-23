def ensure_future(coro_or_future, *, loop=None):
    """Wrap a coroutine or an awaitable in a future.

    If the argument is a Future, it is returned directly.
    """
    if futures.isfuture(coro_or_future):
        if loop is not None and loop is not futures._get_loop(coro_or_future):
            raise ValueError('The future belongs to a different loop than '
                            'the one specified as the loop argument')
        return coro_or_future
    should_close = True
    if not coroutines.iscoroutine(coro_or_future):
        if inspect.isawaitable(coro_or_future):
            async def _wrap_awaitable(awaitable):
                return await awaitable

            coro_or_future = _wrap_awaitable(coro_or_future)
            should_close = False
        else:
            raise TypeError('An asyncio.Future, a coroutine or an awaitable '
                            'is required')

    if loop is None:
        loop = events.get_event_loop()
    try:
        return loop.create_task(coro_or_future)
    except RuntimeError:
        if should_close:
            coro_or_future.close()
        raise