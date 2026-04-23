def get_raster_prep_value(self, value, is_candidate):
        """
        Return a GDALRaster if conversion is successful, otherwise return None.
        """
        if isinstance(value, gdal.GDALRaster):
            return value
        elif is_candidate:
            try:
                return gdal.GDALRaster(value)
            except GDALException:
                pass
        elif isinstance(value, dict):
            try:
                return gdal.GDALRaster(value)
            except GDALException:
                raise ValueError(
                    "Couldn't create spatial object from lookup value '%s'." % value
                )