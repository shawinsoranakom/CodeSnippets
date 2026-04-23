def __rmod__(self, other):
        return self._combine(other, self.MOD, True)