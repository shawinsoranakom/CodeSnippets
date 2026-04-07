def width(self):
        """
        Width (X axis) in pixels of the band.
        """
        return capi.get_band_xsize(self._ptr)