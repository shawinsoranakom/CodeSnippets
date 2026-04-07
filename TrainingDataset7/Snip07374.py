def __rmul__(self, n):
        "multiply"
        return self.__class__(list(self) * n)