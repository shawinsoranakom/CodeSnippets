def covers(self, other):
        """
        Return True if the DE-9IM Intersection Matrix for the two geometries is
        T*****FF*, *T****FF*, ***T**FF*, or ****T*FF*. If either geometry is
        empty, return False.
        """
        return capi.geos_covers(self.ptr, other.ptr)