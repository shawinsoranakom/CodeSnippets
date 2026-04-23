def __reduce__(self):
        raise type(self)("Cannot pickle.")