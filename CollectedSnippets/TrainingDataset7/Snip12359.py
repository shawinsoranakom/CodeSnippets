def __reduce__(self):
        return unpickle_named_row, (names, tuple(self))