def __rand__(self, other):
        return self._combine(other, self.BITAND, True)