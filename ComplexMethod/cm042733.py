def get_func_args_dict(
    func: Callable[..., Any], stripself: bool = False
) -> Mapping[str, inspect.Parameter]:
    """Return the argument dict of a callable object.

    .. versionadded:: 2.14
    """
    if not callable(func):
        raise TypeError(f"func must be callable, got '{type(func).__name__}'")

    args: Mapping[str, inspect.Parameter]
    try:
        sig = inspect.signature(func)
    except ValueError:
        return {}

    if isinstance(func, partial):
        partial_args = func.args
        partial_kw = func.keywords

        args = {}
        for name, param in sig.parameters.items():
            if name in partial_args:
                continue
            if partial_kw and name in partial_kw:
                continue
            args[name] = param
    else:
        args = sig.parameters

    if stripself and args and "self" in args:
        args = {k: v for k, v in args.items() if k != "self"}
    return args