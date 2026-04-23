def equals(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is T*F**FFF*.
        """
        return capi.geos_equals(self.ptr, other.ptr)