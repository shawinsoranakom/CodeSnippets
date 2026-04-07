def __rtruediv__(self, other):
        return self._combine(other, self.DIV, True)