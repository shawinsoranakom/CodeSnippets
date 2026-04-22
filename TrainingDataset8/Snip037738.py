def get_cached_func_name_md(func) -> str:
    """Get markdown representation of the function name."""
    if hasattr(func, "__name__"):
        return "`%s()`" % func.__name__
    elif hasattr(type(func), "__name__"):
        return f"`{type(func).__name__}`"
    return f"`{type(func)}`"