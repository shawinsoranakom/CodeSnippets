def __pow__(self, other):
        return self._combine(other, self.POW, False)