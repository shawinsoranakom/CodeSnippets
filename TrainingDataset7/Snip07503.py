def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.standard < other.standard
        else:
            return NotImplemented