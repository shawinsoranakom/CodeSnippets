def __rpow__(self, other):
        return self._combine(other, self.POW, True)