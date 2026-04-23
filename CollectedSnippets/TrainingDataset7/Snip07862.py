def __invert__(self):
        clone = self.copy()
        clone.invert = not self.invert
        return clone