def centroid(self):
        """Return the centroid (a Point) of this Polygon."""
        # The centroid is a Point, create a geometry for this.
        p = OGRGeometry(OGRGeomType("Point"))
        capi.get_centroid(self.ptr, p.ptr)
        return p