def __ror__(self, other):
        return self._combine(other, self.BITOR, True)