def __rsub__(self, other):
        return self._combine(other, self.SUB, True)