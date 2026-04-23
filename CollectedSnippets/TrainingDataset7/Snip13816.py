def wrapper(func):
        func._screenshot_cases = method_names
        setattr(func, "tags", {"screenshot"}.union(getattr(func, "tags", set())))
        return func