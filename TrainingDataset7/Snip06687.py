def parse_raster(self, value):
        """Convert a PostGIS HEX String into a dict readable by GDALRaster."""
        return from_pgraster(value)