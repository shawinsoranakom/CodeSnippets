def srs(self):
        "Return the OSR SpatialReference for SRID of this Geometry."
        if self.srid:
            try:
                return gdal.SpatialReference(self.srid)
            except (gdal.GDALException, gdal.SRSException):
                pass
        return None