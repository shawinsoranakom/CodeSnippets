def __add__(self, other):
        return self._combine(other, self.ADD, False)