def __invert__(self):
        obj = self.copy()
        obj.negate()
        return obj