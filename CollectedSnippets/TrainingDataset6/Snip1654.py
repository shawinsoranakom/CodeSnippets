def _impartial(func: Callable[..., Any]) -> Callable[..., Any]:
    while isinstance(func, partial):
        func = func.func
    return func