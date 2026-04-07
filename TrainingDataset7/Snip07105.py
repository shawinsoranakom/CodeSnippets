def nodata_value(self, value):
        """
        Set the nodata value for this band.
        """
        if value is None:
            capi.delete_band_nodata_value(self._ptr)
        elif not isinstance(value, (int, float)):
            raise ValueError("Nodata value must be numeric or None.")
        else:
            capi.set_band_nodata_value(self._ptr, value)
        self._flush()