def tuple(self):
        "Return a tuple representation of this Geometry Collection."
        return tuple(self[i].tuple for i in range(self.geom_count))