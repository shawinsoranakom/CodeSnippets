def __new__(cls, *args, warning="ImmutableList object is immutable.", **kwargs):
        self = tuple.__new__(cls, *args, **kwargs)
        self.warning = warning
        return self