def __truediv__(self, other):
        return self._combine(other, self.DIV, False)