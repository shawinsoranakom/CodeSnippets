def tuple(self):
        "Return a tuple of all the coordinates in this Geometry Collection"
        return tuple(g.tuple for g in self)