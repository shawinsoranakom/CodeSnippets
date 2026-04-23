def decorator(func):
            @wraps(func)
            async def inner(*args, **kwargs):
                func_data["func_name"] = getattr(func, "__name__", None)
                func_data["func_module"] = getattr(func, "__module__", None)
                return await func(*args, **kwargs)

            return inner