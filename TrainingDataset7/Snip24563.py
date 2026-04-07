def process_band_indices(self, *args, **kwargs):
                self.band_lhs = self.lhs.band_index
                self.band_rhs, *self.rhs_params = self.rhs_params