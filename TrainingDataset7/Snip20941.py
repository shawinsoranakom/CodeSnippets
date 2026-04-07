async def func(*args, **kwargs):
            await asyncio.sleep(0.01)
            return args, kwargs