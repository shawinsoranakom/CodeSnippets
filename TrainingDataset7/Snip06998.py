def difference(self, other):
        """
        Return a new geometry consisting of the region which is the difference
        of this geometry and the other.
        """
        return self._geomgen(capi.geom_diff, other)