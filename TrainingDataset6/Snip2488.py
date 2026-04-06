def noop_wrap_async(func):
    if inspect.isgeneratorfunction(func):

        @wraps(func)
        async def gen_wrapper(*args, **kwargs):
            async for item in iterate_in_threadpool(func(*args, **kwargs)):
                yield item

        return gen_wrapper

    elif inspect.isasyncgenfunction(func):

        @wraps(func)
        async def async_gen_wrapper(*args, **kwargs):
            async for item in func(*args, **kwargs):
                yield item

        return async_gen_wrapper

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if inspect.isroutine(func) and iscoroutinefunction(func):
            return await func(*args, **kwargs)
        if inspect.isclass(func):
            return await run_in_threadpool(func, *args, **kwargs)
        dunder_call = getattr(func, "__call__", None)  # noqa: B004
        if iscoroutinefunction(dunder_call):
            return await dunder_call(*args, **kwargs)
        return await run_in_threadpool(func, *args, **kwargs)

    return wrapper