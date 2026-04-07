def __eq__(self, other):
        if not isinstance(other, Q):
            return NotImplemented
        return other.identity == self.identity