def __radd__(self, other):
        return self._combine(other, self.ADD, True)