def __repr__(self):
        return (
            f"<{self.__class__.__qualname__} "
            f"model={self.query.model.__qualname__} "
            f"connection={self.connection!r} using={self.using!r}>"
        )