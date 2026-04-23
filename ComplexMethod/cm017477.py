def transform(self, ct, clone=False):
        """
        Requires GDAL. Transform the geometry according to the given
        transformation object, which may be an integer SRID, and WKT or
        PROJ string. By default, transform the geometry in-place and return
        nothing. However if the `clone` keyword is set, don't modify the
        geometry and return a transformed clone instead.
        """
        srid = self.srid

        if ct == srid:
            # short-circuit where source & dest SRIDs match
            if clone:
                return self.clone()
            else:
                return

        if isinstance(ct, gdal.CoordTransform):
            # We don't care about SRID because CoordTransform presupposes
            # source SRS.
            srid = None
        elif srid is None or srid < 0:
            raise GEOSException(
                "Calling transform() with no SRID set is not supported."
            )

        # Creating an OGR Geometry, which is then transformed.
        g = gdal.OGRGeometry(self._ogr_ptr(), srid)
        g.transform(ct)
        # Getting a new GEOS pointer
        ptr = g._geos_ptr()
        if clone:
            # User wants a cloned transformed geometry returned.
            return GEOSGeometry(ptr, srid=g.srid)
        if ptr:
            # Reassigning pointer, and performing post-initialization setup
            # again due to the reassignment.
            capi.destroy_geom(self.ptr)
            self.ptr = ptr
            self._post_init()
            self.srid = g.srid
        else:
            raise GEOSException("Transformed WKB was invalid.")