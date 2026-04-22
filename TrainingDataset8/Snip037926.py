def _get_context(func) -> Context:
    varnames = {}
    if inspect.ismethod(func):
        varnames = {"self": func.__self__}

    return Context(globals=func.__globals__, cells=_Cells(), varnames=varnames)