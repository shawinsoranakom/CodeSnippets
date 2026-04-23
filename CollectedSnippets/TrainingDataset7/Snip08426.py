def __eq__(self, other):
        if not isinstance(other, ValidationError):
            return NotImplemented
        return hash(self) == hash(other)