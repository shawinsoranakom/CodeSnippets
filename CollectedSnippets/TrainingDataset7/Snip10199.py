def __new__(cls, *args, **kwargs):
        # We capture the arguments to make returning them trivial
        self = object.__new__(cls)
        self._constructor_args = (args, kwargs)
        return self