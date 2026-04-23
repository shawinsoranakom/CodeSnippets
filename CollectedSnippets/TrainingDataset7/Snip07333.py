def length(self):
        """
        Return the length of this Geometry (e.g., 0 for point, or the
        circumference of a Polygon).
        """
        return capi.geos_length(self.ptr, byref(c_double()))