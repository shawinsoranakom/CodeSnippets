def process_rhs_params(self):
        if self.rhs_params:
            # Check if a band index was passed in the query argument.
            if len(self.rhs_params) == (2 if self.lookup_name == "relate" else 1):
                self.process_band_indices()
            elif len(self.rhs_params) > 1:
                raise ValueError("Tuple too long for lookup %s." % self.lookup_name)
        elif isinstance(self.lhs, RasterBandTransform):
            self.process_band_indices(only_lhs=True)