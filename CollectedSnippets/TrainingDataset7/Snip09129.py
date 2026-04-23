def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (
            self.limit_value == other.limit_value
            and self.message == other.message
            and self.code == other.code
        )