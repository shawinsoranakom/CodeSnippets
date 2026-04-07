def union(self, other):
        """
        Return a Geometry representing all the points in this Geometry and
        other.
        """
        return self._topology(capi.geos_union(self.ptr, other.ptr))