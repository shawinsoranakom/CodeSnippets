def get_func_args(func):
    params = _get_callable_parameters(func)
    return [param.name for param in params if param.kind in ARG_KINDS]