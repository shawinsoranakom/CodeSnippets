def copy(self):
        c = super().copy()
        c.cases = c.cases[:]
        return c