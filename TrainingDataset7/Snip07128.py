def driver(self):
        """
        Return the GDAL Driver used for this raster.
        """
        ds_driver = capi.get_ds_driver(self._ptr)
        return Driver(ds_driver)