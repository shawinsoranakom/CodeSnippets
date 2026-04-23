def __iadd__(self, other):
        "add another list-like object to self"
        self.extend(other)
        return self