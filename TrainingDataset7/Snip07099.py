def statistics(self, refresh=False, approximate=False):
        """
        Compute statistics on the pixel values of this band.

        The return value is a tuple with the following structure:
        (minimum, maximum, mean, standard deviation).

        If approximate=True, the statistics may be computed based on overviews
        or a subset of image tiles.

        If refresh=True, the statistics will be computed from the data
        directly, and the cache will be updated where applicable.

        For empty bands (where all pixel values are nodata), all statistics
        values are returned as None.

        For raster formats using Persistent Auxiliary Metadata (PAM) services,
        the statistics might be cached in an auxiliary file.
        """
        # Prepare array with arguments for capi function
        smin, smax, smean, sstd = c_double(), c_double(), c_double(), c_double()
        stats_args = [
            self._ptr,
            c_int(approximate),
            byref(smin),
            byref(smax),
            byref(smean),
            byref(sstd),
            c_void_p(),
            c_void_p(),
        ]

        if refresh or self._stats_refresh:
            func = capi.compute_band_statistics
        else:
            # Add additional argument to force computation if there is no
            # existing PAM file to take the values from.
            force = True
            stats_args.insert(2, c_int(force))
            func = capi.get_band_statistics

        # Computation of statistics fails for empty bands.
        try:
            func(*stats_args)
            result = smin.value, smax.value, smean.value, sstd.value
        except GDALException:
            result = (None, None, None, None)

        self._stats_refresh = False

        return result