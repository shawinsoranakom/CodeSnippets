def __imul__(self, n):
        "multiply"
        if n <= 0:
            del self[:]
        else:
            cache = list(self)
            for i in range(n - 1):
                self.extend(cache)
        return self