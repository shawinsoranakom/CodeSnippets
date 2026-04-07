def __repr__(self):
        return (
            f"{self.__class__.__qualname__}(connector={self.connector!r}, "
            f"num_children={self.num_children!r}, negated={self.negated!r})"
        )