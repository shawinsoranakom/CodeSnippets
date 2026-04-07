def __repr__(self):
        return (
            f"<{self.__class__.__qualname__}: "
            f"extra_context={self.extra_context!r} "
            f"singular={self.singular!r} plural={self.plural!r}>"
        )