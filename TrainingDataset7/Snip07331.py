def distance(self, other):
        """
        Return the distance between the closest points on this Geometry
        and the other. Units will be in those of the coordinate system of
        the Geometry.
        """
        if not isinstance(other, GEOSGeometry):
            raise TypeError("distance() works only on other GEOS Geometries.")
        return capi.geos_distance(self.ptr, other.ptr, byref(c_double()))