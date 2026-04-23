def __sub__(self, other):
        return self._combine(other, self.SUB, False)