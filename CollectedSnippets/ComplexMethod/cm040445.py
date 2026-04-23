def _vectorize_apply_excluded(func, excluded, args, kwargs):
    if not excluded:
        return func, args, kwargs

    dynamic_args = [arg for i, arg in enumerate(args) if i not in excluded]
    dynamic_kwargs = {
        key: val for key, val in kwargs.items() if key not in excluded
    }
    static_args = [
        (i, args[i])
        for i in sorted(e for e in excluded if isinstance(e, int))
        if i < len(args)
    ]
    static_kwargs = {key: val for key, val in kwargs.items() if key in excluded}

    def new_func(*args, **kwargs):
        args = list(args)
        for i, arg in static_args:
            args.insert(i, arg)
        return func(*args, **kwargs, **static_kwargs)

    return new_func, dynamic_args, dynamic_kwargs