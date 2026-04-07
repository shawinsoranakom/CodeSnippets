def __eq__(self, other):
        if not isinstance(other, BaseTable):
            return NotImplemented
        return self.identity == other.identity