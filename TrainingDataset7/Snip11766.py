def __eq__(self, other):
        if self.__class__ == other.__class__:
            return self.deconstruct() == other.deconstruct()
        return NotImplemented