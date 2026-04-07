def _flush(self):
        """
        Flush all data from memory into the source file if it exists.
        The data that needs flushing are geotransforms, coordinate systems,
        nodata_values and pixel values. This function will be called
        automatically wherever it is needed.
        """
        # Raise an Exception if the value is being changed in read mode.
        if not self._write:
            raise GDALException(
                "Raster needs to be opened in write mode to change values."
            )
        capi.flush_ds(self._ptr)