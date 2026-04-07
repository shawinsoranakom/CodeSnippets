def buffer(self, width, quadsegs=8):
        """
        Return a geometry that represents all points whose distance from this
        Geometry is less than or equal to distance. Calculations are in the
        Spatial Reference System of this Geometry. The optional third parameter
        sets the number of segment used to approximate a quarter circle
        (defaults to 8). (Text from PostGIS documentation at ch. 6.1.3)
        """
        return self._topology(capi.geos_buffer(self.ptr, width, quadsegs))