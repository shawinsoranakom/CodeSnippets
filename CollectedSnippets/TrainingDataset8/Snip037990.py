def _get_top_level_module(func: Callable[..., Any]) -> str:
    """Get the top level module for the given function."""
    module = inspect.getmodule(func)
    if module is None or not module.__name__:
        return "unknown"
    return module.__name__.split(".")[0]