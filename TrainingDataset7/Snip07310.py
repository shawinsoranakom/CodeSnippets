def _ogr_ptr(self):
        return gdal.OGRGeometry._from_wkb(self.wkb)