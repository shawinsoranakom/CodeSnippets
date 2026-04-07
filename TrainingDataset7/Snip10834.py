def __contains__(self, other):
        # Disable old-style iteration protocol inherited from implementing
        # __getitem__() to prevent this method from hanging.
        raise TypeError(f"argument of type '{self.__class__.__name__}' is not iterable")