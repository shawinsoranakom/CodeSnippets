def __eq__(self, other):
        if not isinstance(other, Join):
            return NotImplemented
        return self.identity == other.identity