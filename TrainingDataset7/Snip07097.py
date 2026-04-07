def height(self):
        """
        Height (Y axis) in pixels of the band.
        """
        return capi.get_band_ysize(self._ptr)