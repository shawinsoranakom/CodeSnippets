def Extract(self, features, num_features_per_region=None):
    """Extracts aggregated representation.

    Args:
      features: [N, D] float numpy array with N local feature descriptors.
      num_features_per_region: Required only if computing regional aggregated
        representations, otherwise optional. List of number of features per
        region, such that sum(num_features_per_region) = N. It indicates which
        features correspond to each region.

    Returns:
      aggregated_descriptors: 1-D numpy array.
      feature_visual_words: Used only for ASMK/ASMK* aggregation type. 1-D
        numpy array denoting visual words corresponding to the
        `aggregated_descriptors`.

    Raises:
      ValueError: If inputs are misconfigured.
    """
    features = tf.cast(features, dtype=tf.float32)

    if num_features_per_region is None:
      # Use dummy value since it is unused.
      num_features_per_region = []
    else:
      num_features_per_region = tf.cast(num_features_per_region, dtype=tf.int32)
      if len(num_features_per_region
            ) and sum(num_features_per_region) != features.shape[0]:
        raise ValueError(
            "Incorrect arguments: sum(num_features_per_region) and "
            "features.shape[0] are different: %d vs %d" %
            (sum(num_features_per_region), features.shape[0]))

    # Extract features based on desired options.
    if self._aggregation_type == _VLAD:
      # Feature visual words are unused in the case of VLAD, so just return
      # dummy constant.
      feature_visual_words = tf.constant(-1, dtype=tf.int32)
      if self._use_regional_aggregation:
        aggregated_descriptors = self._ComputeRvlad(
            features,
            num_features_per_region,
            self._codebook,
            use_l2_normalization=self._use_l2_normalization,
            num_assignments=self._num_assignments)
      else:
        aggregated_descriptors = self._ComputeVlad(
            features,
            self._codebook,
            use_l2_normalization=self._use_l2_normalization,
            num_assignments=self._num_assignments)
    elif (self._aggregation_type == _ASMK or
          self._aggregation_type == _ASMK_STAR):
      if self._use_regional_aggregation:
        (aggregated_descriptors,
         feature_visual_words) = self._ComputeRasmk(
             features,
             num_features_per_region,
             self._codebook,
             num_assignments=self._num_assignments)
      else:
        (aggregated_descriptors,
         feature_visual_words) = self._ComputeAsmk(
             features,
             self._codebook,
             num_assignments=self._num_assignments)

    feature_visual_words_output = feature_visual_words.numpy()

    # If using ASMK*/RASMK*, binarize the aggregated descriptors.
    if self._aggregation_type == _ASMK_STAR:
      reshaped_aggregated_descriptors = np.reshape(
          aggregated_descriptors, [-1, self._feature_dimensionality])
      packed_descriptors = np.packbits(
          reshaped_aggregated_descriptors > 0, axis=1)
      aggregated_descriptors_output = np.reshape(packed_descriptors, [-1])
    else:
      aggregated_descriptors_output = aggregated_descriptors.numpy()

    return aggregated_descriptors_output, feature_visual_words_output