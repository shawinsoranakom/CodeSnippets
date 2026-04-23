def __eq__(self, other):
        if not isinstance(other, Lookup):
            return NotImplemented
        return self.identity == other.identity