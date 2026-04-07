def lists_of_len(self, length=None):
        if length is None:
            length = self.limit
        pl = list(range(length))
        return pl, self.listType(pl)