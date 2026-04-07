def equals_exact(self, other, tolerance=0):
        """
        Return true if the two Geometries are exactly equal, up to a
        specified tolerance.
        """
        return capi.geos_equalsexact(self.ptr, other.ptr, float(tolerance))