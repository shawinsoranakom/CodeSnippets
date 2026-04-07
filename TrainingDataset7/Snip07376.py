def __eq__(self, other):
        olen = len(other)
        for i in range(olen):
            try:
                c = self[i] == other[i]
            except IndexError:
                # self must be shorter
                return False
            if not c:
                return False
        return len(self) == olen