async def wrapper(*args, **kwargs):
        if inspect.isroutine(func) and iscoroutinefunction(func):
            return await func(*args, **kwargs)
        if inspect.isclass(func):
            return await run_in_threadpool(func, *args, **kwargs)
        dunder_call = getattr(func, "__call__", None)  # noqa: B004
        if iscoroutinefunction(dunder_call):
            return await dunder_call(*args, **kwargs)
        return await run_in_threadpool(func, *args, **kwargs)