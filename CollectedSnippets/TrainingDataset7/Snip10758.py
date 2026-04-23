def __mod__(self, other):
        return self._combine(other, self.MOD, False)