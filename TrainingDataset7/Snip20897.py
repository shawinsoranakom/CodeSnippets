def async_simple_dec(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        return f"returned: {result}"

    return wrapper