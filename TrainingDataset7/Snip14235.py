def replace(obj, /, **changes):
        """Return a new object replacing specified fields with new values.

        This is especially useful for immutable objects, like named tuples or
        frozen dataclasses.
        """
        cls = obj.__class__
        func = getattr(cls, "__replace__", None)
        if func is None:
            raise TypeError(f"replace() does not support {cls.__name__} objects")
        return func(obj, **changes)