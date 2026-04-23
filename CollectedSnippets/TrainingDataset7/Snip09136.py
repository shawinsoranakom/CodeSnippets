def compare(self, a, b):
        offset = 0 if self.offset is None else self.offset
        return not math.isclose(math.remainder(a - offset, b), 0, abs_tol=1e-9)