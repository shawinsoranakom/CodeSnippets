def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.alias!r}, {self.targets!r}, "
            f"{self.sources!r}, {self.output_field!r})"
        )