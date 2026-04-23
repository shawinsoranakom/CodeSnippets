def geotransform(self):
        """
        Return the geotransform of the data source.
        Return the default geotransform if it does not exist or has not been
        set previously. The default is [0.0, 1.0, 0.0, 0.0, 0.0, -1.0].
        """
        # Create empty ctypes double array for data
        gtf = (c_double * 6)()
        capi.get_ds_geotransform(self._ptr, byref(gtf))
        return list(gtf)