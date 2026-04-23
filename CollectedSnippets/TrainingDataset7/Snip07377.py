def __lt__(self, other):
        olen = len(other)
        for i in range(olen):
            try:
                c = self[i] < other[i]
            except IndexError:
                # self must be shorter
                return True
            if c:
                return c
            elif other[i] < self[i]:
                return False
        return len(self) < olen