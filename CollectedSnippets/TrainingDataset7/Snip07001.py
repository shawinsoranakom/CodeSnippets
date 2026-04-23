def union(self, other):
        """
        Return a new geometry consisting of the region which is the union of
        this geometry and the other.
        """
        return self._geomgen(capi.geom_union, other)