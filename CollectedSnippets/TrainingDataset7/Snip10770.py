def __rmul__(self, other):
        return self._combine(other, self.MUL, True)