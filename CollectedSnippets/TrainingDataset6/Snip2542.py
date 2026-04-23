async def async_gen_wrapper(*args, **kwargs):
            async for item in func(*args, **kwargs):
                yield item