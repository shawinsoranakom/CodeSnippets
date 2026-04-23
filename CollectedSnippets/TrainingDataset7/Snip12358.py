def create_namedtuple_class(*names):
    # Cache type() with @lru_cache since it's too slow to be called for every
    # QuerySet evaluation.
    def __reduce__(self):
        return unpickle_named_row, (names, tuple(self))

    return type(
        "Row",
        (namedtuple("Row", names),),
        {"__reduce__": __reduce__, "__slots__": ()},
    )