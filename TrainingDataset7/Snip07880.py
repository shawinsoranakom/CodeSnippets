def __invert__(self):
        # Apply De Morgan's theorem.
        cloned = self.copy()
        cloned.connector = self.BITAND if self.connector == self.BITOR else self.BITOR
        cloned.lhs = ~self.lhs
        cloned.rhs = ~self.rhs
        return cloned