def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.identity == other.identity