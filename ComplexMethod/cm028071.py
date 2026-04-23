def _AsmkSimilarity(self,
                      aggregated_descriptors_1,
                      aggregated_descriptors_2,
                      visual_words_1,
                      visual_words_2,
                      binarized=False):
    """Compute ASMK-based similarity.

    If `aggregated_descriptors_1` or `aggregated_descriptors_2` is empty, we
    return a similarity of -1.0.

    If binarized is True, `aggregated_descriptors_1` and
    `aggregated_descriptors_2` must be of type uint8.

    Args:
      aggregated_descriptors_1: 1-D NumPy array.
      aggregated_descriptors_2: 1-D NumPy array.
      visual_words_1: 1-D sorted NumPy integer array denoting visual words
        corresponding to `aggregated_descriptors_1`.
      visual_words_2: 1-D sorted NumPy integer array denoting visual words
        corresponding to `aggregated_descriptors_2`.
      binarized: If True, compute ASMK* similarity.

    Returns:
      similarity: Float. The larger, the more similar.

    Raises:
      ValueError: If input descriptor dimensionality is inconsistent, or if
        descriptor type is unsupported.
    """
    num_visual_words_1 = len(visual_words_1)
    num_visual_words_2 = len(visual_words_2)

    if not num_visual_words_1 or not num_visual_words_2:
      return -1.0

    # Parse dimensionality used per visual word. They must be the same for both
    # aggregated descriptors. If using ASMK, they also must be equal to
    # self._feature_dimensionality.
    if binarized:
      if aggregated_descriptors_1.dtype != 'uint8':
        raise ValueError('Incorrect input descriptor type: %s' %
                         aggregated_descriptors_1.dtype)
      if aggregated_descriptors_2.dtype != 'uint8':
        raise ValueError('Incorrect input descriptor type: %s' %
                         aggregated_descriptors_2.dtype)

      per_visual_word_dimensionality = int(
          len(aggregated_descriptors_1) / num_visual_words_1)
      if len(aggregated_descriptors_2
            ) / num_visual_words_2 != per_visual_word_dimensionality:
        raise ValueError('ASMK* dimensionality is inconsistent.')
    else:
      per_visual_word_dimensionality = self._feature_dimensionality
      self._CheckAsmkDimensionality(aggregated_descriptors_1,
                                    num_visual_words_1, '1')
      self._CheckAsmkDimensionality(aggregated_descriptors_2,
                                    num_visual_words_2, '2')

    aggregated_descriptors_1_reshape = np.reshape(
        aggregated_descriptors_1,
        [num_visual_words_1, per_visual_word_dimensionality])
    aggregated_descriptors_2_reshape = np.reshape(
        aggregated_descriptors_2,
        [num_visual_words_2, per_visual_word_dimensionality])

    # Loop over visual words, compute similarity.
    unnormalized_similarity = 0.0
    ind_1 = 0
    ind_2 = 0
    while ind_1 < num_visual_words_1 and ind_2 < num_visual_words_2:
      if visual_words_1[ind_1] == visual_words_2[ind_2]:
        if binarized:
          inner_product = self._BinaryNormalizedInnerProduct(
              aggregated_descriptors_1_reshape[ind_1],
              aggregated_descriptors_2_reshape[ind_2])
        else:
          inner_product = np.dot(aggregated_descriptors_1_reshape[ind_1],
                                 aggregated_descriptors_2_reshape[ind_2])
        unnormalized_similarity += self._SigmaFn(inner_product)
        ind_1 += 1
        ind_2 += 1
      elif visual_words_1[ind_1] > visual_words_2[ind_2]:
        ind_2 += 1
      else:
        ind_1 += 1

    final_similarity = unnormalized_similarity
    if self._use_l2_normalization:
      final_similarity /= np.sqrt(num_visual_words_1 * num_visual_words_2)

    return final_similarity