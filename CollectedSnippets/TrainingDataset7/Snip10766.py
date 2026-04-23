def __or__(self, other):
        if getattr(self, "conditional", False) and getattr(other, "conditional", False):
            return Q(self) | Q(other)
        raise NotImplementedError(
            "Use .bitand(), .bitor(), and .bitxor() for bitwise logical operations."
        )