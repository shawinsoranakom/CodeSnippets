def info(self):
        """
        Return information about this raster in a string format equivalent
        to the output of the gdalinfo command line utility.
        """
        return capi.get_ds_info(self.ptr, None).decode()