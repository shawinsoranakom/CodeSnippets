async def gen_wrapper(*args, **kwargs):
            async for item in iterate_in_threadpool(func(*args, **kwargs)):
                yield item