def __subclasscheck__(self, subclass):
        return issubclass(subclass, self._subclasses) or super().__subclasscheck__(
            subclass
        )