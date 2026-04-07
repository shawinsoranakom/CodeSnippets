def color_interp(self, as_string=False):
        """Return the GDAL color interpretation for this band."""
        color = capi.get_band_color_interp(self._ptr)
        if as_string:
            color = GDAL_COLOR_TYPES[color]
        return color