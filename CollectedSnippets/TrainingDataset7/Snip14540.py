def _get_func_parameters(func, remove_first):
    parameters = tuple(signature(func).parameters.values())
    if remove_first:
        parameters = parameters[1:]
    return parameters