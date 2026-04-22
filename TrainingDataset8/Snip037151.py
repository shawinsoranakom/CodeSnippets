async def async_for():
    async def async_iter():
        yield

    async for _ in async_iter():
        "ASYNC FOR"