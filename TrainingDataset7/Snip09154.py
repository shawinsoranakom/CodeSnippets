def __repr__(self):
        return (
            f"<{self.__class__.__qualname__} "
            f"vendor={self.vendor!r} alias={self.alias!r}>"
        )