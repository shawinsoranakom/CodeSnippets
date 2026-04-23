def screenshot_cases(method_names):
    if isinstance(method_names, str):
        method_names = method_names.split(",")

    def wrapper(func):
        func._screenshot_cases = method_names
        setattr(func, "tags", {"screenshot"}.union(getattr(func, "tags", set())))
        return func

    return wrapper