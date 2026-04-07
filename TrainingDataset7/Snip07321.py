def difference(self, other):
        """
        Return a Geometry representing the points making up this Geometry
        that do not make up other.
        """
        return self._topology(capi.geos_difference(self.ptr, other.ptr))