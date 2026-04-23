def name(self):
        """
        Return the name of this raster. Corresponds to filename
        for file-based rasters.
        """
        return force_str(capi.get_ds_description(self._ptr))