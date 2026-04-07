def ogr(self):
        "Return the OGR Geometry for this Geometry."
        return gdal.OGRGeometry(self._ogr_ptr(), self.srs)