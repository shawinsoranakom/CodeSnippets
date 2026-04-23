def _make_feature(self, feat_id):
        """
        Helper routine for __getitem__ that constructs a Feature from the given
        Feature ID. If the OGR Layer does not support random-access reading,
        then each feature of the layer will be incremented through until the
        a Feature is found matching the given feature ID.
        """
        if self._random_read:
            # If the Layer supports random reading, return.
            try:
                return Feature(capi.get_feature(self.ptr, feat_id), self)
            except GDALException:
                pass
        else:
            # Random access isn't supported, have to increment through
            # each feature until the given feature ID is encountered.
            for feat in self:
                if feat.fid == feat_id:
                    return feat
        # Should have returned a Feature, raise an IndexError.
        raise IndexError("Invalid feature id: %s." % feat_id)