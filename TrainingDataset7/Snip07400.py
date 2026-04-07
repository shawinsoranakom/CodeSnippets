def _ogr_ptr(self):
        return (
            gdal.geometries.Point._create_empty() if self.empty else super()._ogr_ptr()
        )