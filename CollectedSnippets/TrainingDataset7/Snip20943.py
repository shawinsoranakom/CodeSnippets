def myattr2_dec(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            wrapper.myattr2 = True
            return wrapper