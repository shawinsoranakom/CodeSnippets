def _normalize(self) -> None:
        """Compile all original and normalized alignments"""
        logger.debug("Normalize")
        count = sum(1 for val in self._alignments.data.values() if val.faces)

        sample_lm = next((val.faces[0].landmarks_xy
                          for val in self._alignments.data.values() if val.faces), 68)
        assert isinstance(sample_lm, np.ndarray)
        lm_count = sample_lm.shape[0]
        if lm_count != 68:
            raise FaceswapError("Spatial smoothing only supports 68 point facial landmarks")

        landmarks_all = np.zeros((lm_count, 2, int(count)))

        end = 0
        for key in tqdm(sorted(self._alignments.data.keys()), desc="Compiling", leave=False):
            val = self._alignments.data[key].faces
            if not val:
                continue
            # We should only be normalizing a single face, so just take
            # the first landmarks found
            landmarks = np.array(val[0].landmarks_xy).reshape((lm_count, 2, 1))
            start = end
            end = start + landmarks.shape[2]
            # Store in one big array
            landmarks_all[:, :, start:end] = landmarks
            # Make sure we keep track of the mapping to the original frame
            self._mappings[start] = key

        # Normalize shapes
        normalized_shape = self._normalize_shapes(landmarks_all)
        self._normalized["landmarks"] = normalized_shape[0]
        self._normalized["scale_factors"] = normalized_shape[1]
        self._normalized["mean_coords"] = normalized_shape[2]
        logger.debug("Normalized: %s", self._normalized)