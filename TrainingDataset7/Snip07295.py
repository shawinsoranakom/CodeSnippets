def overlaps(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is T*T***T** (for two points or two surfaces) 1*T***T** (for two
        curves).
        """
        return capi.geos_overlaps(self.ptr, other.ptr)