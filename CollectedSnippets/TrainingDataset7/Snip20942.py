def myattr_dec(func):
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            wrapper.myattr = True
            return wrapper