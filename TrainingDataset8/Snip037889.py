def _calling_cached_function(func: Callable[..., Any]) -> Iterator[None]:
    _cache_info.cached_func_stack.append(func)
    try:
        yield
    finally:
        _cache_info.cached_func_stack.pop()