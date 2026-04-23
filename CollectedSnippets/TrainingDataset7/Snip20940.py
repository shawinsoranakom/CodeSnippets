def decorator(func):
            @wraps(func)
            def inner(*args, **kwargs):
                nonlocal func_name, func_module
                func_name = getattr(func, "__name__", None)
                func_module = getattr(func, "__module__", None)
                return func(*args, **kwargs)

            return inner