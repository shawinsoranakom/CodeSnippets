def __set_name__(self, owner, name):
        func = getattr(owner._wrapped__, name)
        descriptor = inspect.getattr_static(owner._wrapped__, name)
        cast = self._cast__

        if isinstance(descriptor, staticmethod):
            if cast:
                def wrap_func(*args, **kwargs):
                    result = func(*args, **kwargs)
                    return cast(result) if result is not None else None
            elif cast is None:
                def wrap_func(*args, **kwargs):
                    func(*args, **kwargs)
            else:
                def wrap_func(*args, **kwargs):
                    return func(*args, **kwargs)

            functools.update_wrapper(wrap_func, func)
            wrap_func = staticmethod(wrap_func)

        elif isinstance(descriptor, classmethod):
            if cast:
                def wrap_func(cls, *args, **kwargs):
                    result = func(*args, **kwargs)
                    return cast(result) if result is not None else None
            elif cast is None:
                def wrap_func(cls, *args, **kwargs):
                    func(*args, **kwargs)
            else:
                def wrap_func(cls, *args, **kwargs):
                    return func(*args, **kwargs)

            functools.update_wrapper(wrap_func, func)
            wrap_func = classmethod(wrap_func)

        else:
            if cast:
                def wrap_func(self, *args, **kwargs):
                    result = func(self._wrapped__, *args, **kwargs)
                    return cast(result) if result is not None else None
            elif cast is None:
                def wrap_func(self, *args, **kwargs):
                    func(self._wrapped__, *args, **kwargs)
            else:
                def wrap_func(self, *args, **kwargs):
                    return func(self._wrapped__, *args, **kwargs)

            functools.update_wrapper(wrap_func, func)

        setattr(owner, name, wrap_func)