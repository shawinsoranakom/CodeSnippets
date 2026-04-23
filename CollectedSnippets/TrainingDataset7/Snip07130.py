def height(self):
        """
        Height (Y axis) in pixels.
        """
        return capi.get_ds_ysize(self._ptr)