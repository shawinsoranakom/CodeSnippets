def __or__(self, other):
        "Return the union of this Geometry and the other."
        return self.union(other)