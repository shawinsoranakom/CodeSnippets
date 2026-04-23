def width(self):
        """
        Width (X axis) in pixels.
        """
        return capi.get_ds_xsize(self._ptr)