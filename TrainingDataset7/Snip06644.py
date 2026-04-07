def getquoted(self):
        """
        Return a properly quoted string for use in PostgreSQL/PostGIS.
        """
        if self.is_geometry:
            # Psycopg will figure out whether to use E'\\000' or '\000'.
            return b"%s(%s)" % (
                b"ST_GeogFromWKB" if self.geography else b"ST_GeomFromEWKB",
                sql.quote(self.ewkb).encode(),
            )
        else:
            # For rasters, add explicit type cast to WKB string.
            return b"'%s'::raster" % self.ewkb.hex().encode()