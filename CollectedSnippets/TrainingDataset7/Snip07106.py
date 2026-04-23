def datatype(self, as_string=False):
        """
        Return the GDAL Pixel Datatype for this band.
        """
        dtype = capi.get_band_datatype(self._ptr)
        if as_string:
            dtype = GDAL_PIXEL_TYPES[dtype]
        return dtype