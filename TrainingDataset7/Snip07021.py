def tuple(self):
        "Return a tuple of LinearRing coordinate tuples."
        return tuple(self[i].tuple for i in range(self.geom_count))