def inner(*args, **kwargs):
                with self as context:
                    if self.kwarg_name:
                        kwargs[self.kwarg_name] = context
                    return func(*args, **kwargs)