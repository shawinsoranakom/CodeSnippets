def crosses(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is T*T****** (for a point and a curve,a point and an area or a line and
        an area) 0******** (for two curves).
        """
        return capi.geos_crosses(self.ptr, other.ptr)