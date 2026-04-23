def get_param_names(fn, n_args):
    if isinstance(fn, OpOverloadPacket):
        fn = fn.op

    if (
        not is_function_or_method(fn)
        and callable(fn)
        and is_function_or_method(fn.__call__)
    ):
        # De-sugar calls to classes
        fn = fn.__call__

    if is_function_or_method(fn):
        if is_ignored_fn(fn):
            fn = inspect.unwrap(fn)
        return inspect.getfullargspec(fn).args
    else:
        # The `fn` was not a method or function (maybe a class with a __call__
        # method, so use a default param name list)
        return [str(i) for i in range(n_args)]