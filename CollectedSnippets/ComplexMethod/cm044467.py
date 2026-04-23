def __call__(self, batch: ExtractBatch) -> None:
        """Apply aligner filters to the given batch

        Parameters
        ----------
        batch
            The batch object to perform filtering on with the landmarks populated
        """
        if not self.enabled or batch.landmarks is None:
            return
        if batch.landmark_type not in (LandmarkType.LM_2D_68, LandmarkType.LM_2D_98):
            logger.warning("[Align filter] Filters are not supported for %s landmarks",
                           batch.landmark_type)
            self.enabled = False
            return
        if self._features:
            self._handle_filtered("features",
                                  batch,
                                  self._filter_features(batch.aligned.landmarks_normalized))
        if self._min_scale > 0.0 or self._max_scale > 0.0:
            self._handle_filtered("scale", batch, self._filter_scale(batch))
        if self._distance > 0.0:
            d_msk = np.abs(batch.aligned.landmarks_normalized[:, 17:] -
                           self._mean_face).mean(axis=(1, 2)) <= self._distance
            self._handle_filtered("distance", batch, d_msk)
        if self._roll > 0.0:
            r_msk = np.abs(Batch3D.roll(batch.aligned.rotation)) <= self._roll
            self._handle_filtered("roll", batch, r_msk)