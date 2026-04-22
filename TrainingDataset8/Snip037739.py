def get_return_value_type(return_value) -> str:
    if hasattr(return_value, "__module__") and hasattr(type(return_value), "__name__"):
        return f"`{return_value.__module__}.{type(return_value).__name__}`"
    return get_cached_func_name_md(return_value)