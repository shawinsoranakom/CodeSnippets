def intersection(self, other):
        """
        Return a new geometry consisting of the region of intersection of this
        geometry and the other.
        """
        return self._geomgen(capi.geom_intersection, other)