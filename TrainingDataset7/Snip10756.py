def __mul__(self, other):
        return self._combine(other, self.MUL, False)