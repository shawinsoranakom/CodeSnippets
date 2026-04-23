def touches(self, other):
        """
        Return true if the DE-9IM intersection matrix for the two Geometries
        is FT*******, F**T***** or F***T****.
        """
        return capi.geos_touches(self.ptr, other.ptr)