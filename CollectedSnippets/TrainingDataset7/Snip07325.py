def relate(self, other):
        """
        Return the DE-9IM intersection matrix for this Geometry and the other.
        """
        return capi.geos_relate(self.ptr, other.ptr).decode()