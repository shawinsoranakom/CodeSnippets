def empty(self):
        """
        Return a boolean indicating whether the set of points in this Geometry
        are empty.
        """
        return capi.geos_isempty(self.ptr)