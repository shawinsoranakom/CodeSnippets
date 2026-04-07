def __call__(self, func):
        # Note that we are intentionally not using @wraps here for performance
        # reasons. Refs #21109.
        def inner(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return inner