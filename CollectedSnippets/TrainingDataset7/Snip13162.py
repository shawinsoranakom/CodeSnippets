def __eq__(self, other):
        return (
            isinstance(other, Origin)
            and self.name == other.name
            and self.loader == other.loader
        )