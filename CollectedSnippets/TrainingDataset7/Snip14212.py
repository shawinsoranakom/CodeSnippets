def __eq__(self, other):
        if isinstance(other, Iterable):
            return all(a == b for a, b in zip_longest(self, other, fillvalue=object()))
        return super().__eq__(other)