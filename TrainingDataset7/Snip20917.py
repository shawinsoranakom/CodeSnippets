async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        return f"returned: {result}"