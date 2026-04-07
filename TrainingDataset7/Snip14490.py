def wrapper(*args, **kwargs):
            if any(
                isinstance(arg, Promise)
                for arg in itertools.chain(args, kwargs.values())
            ):
                return lazy_func(*args, **kwargs)
            return func(*args, **kwargs)