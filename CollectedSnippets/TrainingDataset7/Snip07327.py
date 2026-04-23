def sym_difference(self, other):
        """
        Return a set combining the points in this Geometry not in other,
        and the points in other not in this Geometry.
        """
        return self._topology(capi.geos_symdifference(self.ptr, other.ptr))