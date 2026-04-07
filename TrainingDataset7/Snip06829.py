def process_band_indices(self, only_lhs=False):
        """
        Extract the lhs band index from the band transform class and the rhs
        band index from the input tuple.
        """
        # PostGIS band indices are 1-based, so the band index needs to be
        # increased to be consistent with the GDALRaster band indices.
        if only_lhs:
            self.band_rhs = 1
            self.band_lhs = self.lhs.band_index + 1
            return

        if isinstance(self.lhs, RasterBandTransform):
            self.band_lhs = self.lhs.band_index + 1
        else:
            self.band_lhs = 1

        self.band_rhs, *self.rhs_params = self.rhs_params