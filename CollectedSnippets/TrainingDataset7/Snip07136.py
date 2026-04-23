def geotransform(self, values):
        "Set the geotransform for the data source."
        if len(values) != 6 or not all(isinstance(x, (int, float)) for x in values):
            raise ValueError("Geotransform must consist of 6 numeric values.")
        # Create ctypes double array with input and write data
        values = (c_double * 6)(*values)
        capi.set_ds_geotransform(self._ptr, byref(values))
        self._flush()