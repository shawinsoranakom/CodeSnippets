def centroid(self):
        """
        The centroid is equal to the centroid of the set of component
        Geometries of highest dimension (since the lower-dimension geometries
        contribute zero "weight" to the centroid).
        """
        return self._topology(capi.geos_centroid(self.ptr))