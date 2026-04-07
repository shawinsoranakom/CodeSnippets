def __eq__(self, other):
        return isinstance(other, Mapping) and {
            k.lower(): v for k, v in self.items()
        } == {k.lower(): v for k, v in other.items()}