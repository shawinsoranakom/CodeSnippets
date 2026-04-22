def clear():
        """Clear the wrapped function's associated cache."""
        cache = cached_func.get_function_cache(function_key)
        cache.clear()