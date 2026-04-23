def within(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is T*F**F***.
        """
        return capi.geos_within(self.ptr, other.ptr)