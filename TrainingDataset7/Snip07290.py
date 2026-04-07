def disjoint(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is FF*FF****.
        """
        return capi.geos_disjoint(self.ptr, other.ptr)