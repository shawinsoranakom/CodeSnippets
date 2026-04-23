def __eq__(self, other):
        if not isinstance(other, RegexObject):
            return NotImplemented
        return self.pattern == other.pattern and self.flags == other.flags