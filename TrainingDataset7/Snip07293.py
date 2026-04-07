def equals_identical(self, other):
        """
        Return true if the two Geometries are point-wise equivalent.
        """
        if geos_version_tuple() < (3, 12):
            raise GEOSException(
                "GEOSGeometry.equals_identical() requires GEOS >= 3.12.0."
            )
        return capi.geos_equalsidentical(self.ptr, other.ptr)