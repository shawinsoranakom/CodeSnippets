def intersection(self, other):
        """
        Return a Geometry representing the points shared by this Geometry and
        other.
        """
        return self._topology(capi.geos_intersection(self.ptr, other.ptr))