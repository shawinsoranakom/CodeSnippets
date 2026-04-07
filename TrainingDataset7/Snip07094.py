def _flush(self):
        """
        Call the flush method on the Band's parent raster and force a refresh
        of the statistics attribute when requested the next time.
        """
        self.source._flush()
        self._stats_refresh = True