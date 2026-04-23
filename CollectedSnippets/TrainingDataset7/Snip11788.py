def __hash__(self):
        return hash(make_hashable(self.identity))