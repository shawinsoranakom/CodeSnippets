def get_function_nonlocals(func: Callable) -> list[Any]:
    """Get the nonlocal variables accessed by a function.

    Args:
        func: The function to check.

    Returns:
        The nonlocal variables accessed by the function.
    """
    try:
        code = inspect.getsource(func)
        tree = ast.parse(textwrap.dedent(code))
        visitor = FunctionNonLocals()
        visitor.visit(tree)
        values: list[Any] = []
        closure = (
            inspect.getclosurevars(func.__wrapped__)
            if hasattr(func, "__wrapped__") and callable(func.__wrapped__)
            else inspect.getclosurevars(func)
        )
        candidates = {**closure.globals, **closure.nonlocals}
        for k, v in candidates.items():
            if k in visitor.nonlocals:
                values.append(v)
            for kk in visitor.nonlocals:
                if "." in kk and kk.startswith(k):
                    vv = v
                    for part in kk.split(".")[1:]:
                        if vv is None:
                            break
                        try:
                            vv = getattr(vv, part)
                        except AttributeError:
                            break
                    else:
                        values.append(vv)
    except (SyntaxError, TypeError, OSError, SystemError):
        return []

    return values