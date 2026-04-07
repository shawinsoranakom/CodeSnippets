def description(self):
        """
        Return the description string of the band.
        """
        return force_str(capi.get_band_description(self._ptr))