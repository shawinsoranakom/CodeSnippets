def __torch_function__(cls, func, types, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        # Find an instance of this class in the arguments
        args_of_this_cls = []
        for a in args:
            if isinstance(a, cls):
                args_of_this_cls.append(a)
            elif isinstance(a, collections.abc.Sequence):
                args_of_this_cls.extend(el for el in a if isinstance(el, cls))
        if len(args_of_this_cls) <= 0:
            raise AssertionError("expected args_of_this_cls to be non-empty")
        for a in args_of_this_cls:
            a.used_calls.add(func)
        args = unwrap(tuple(args))
        kwargs = {k: unwrap(v) for k, v in kwargs.items()}

        return wrap(func(*args, **kwargs))