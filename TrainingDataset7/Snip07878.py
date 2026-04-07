def __invert__(self):
        cloned = self.copy()
        cloned.invert = not self.invert
        return cloned