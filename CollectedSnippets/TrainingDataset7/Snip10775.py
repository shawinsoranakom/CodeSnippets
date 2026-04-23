def __ror__(self, other):
        raise NotImplementedError(
            "Use .bitand(), .bitor(), and .bitxor() for bitwise logical operations."
        )