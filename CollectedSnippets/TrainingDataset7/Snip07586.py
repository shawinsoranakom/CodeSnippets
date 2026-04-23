def __eq__(self, other):
        if not isinstance(other, Message):
            return NotImplemented
        return self.level == other.level and self.message == other.message