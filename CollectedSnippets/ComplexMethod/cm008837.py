def cli_configuration_args(argdict, keys, default=[], use_compat=True):
    if isinstance(argdict, (list, tuple)):  # for backward compatibility
        if use_compat:
            return argdict
        else:
            argdict = None
    if argdict is None:
        return default
    assert isinstance(argdict, dict)

    assert isinstance(keys, (list, tuple))
    for key_list in keys:
        arg_list = list(filter(
            lambda x: x is not None,
            [argdict.get(key.lower()) for key in variadic(key_list)]))
        if arg_list:
            return [arg for args in arg_list for arg in args]
    return default