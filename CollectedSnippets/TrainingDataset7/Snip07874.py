def __and__(self, other):
        return self._combine(other, self.BITAND, False)