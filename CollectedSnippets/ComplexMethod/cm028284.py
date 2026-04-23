def _build_context_features(self, example_list):
    context_features = []
    context_features_image_id_list = []
    count = 0
    example_embedding = []

    for idx, example in enumerate(example_list):
      if self._subsample_context_features_rate > 0:
        if (idx % self._subsample_context_features_rate) != 0:
          example.features.feature[
              'context_features_idx'].int64_list.value.append(
                  self._max_num_elements_in_context_features + 1)
          continue
      if self._keep_only_positives:
        if example.features.feature[
            'image/embedding_score'
            ].float_list.value[0] < self._context_features_score_threshold:
          example.features.feature[
              'context_features_idx'].int64_list.value.append(
                  self._max_num_elements_in_context_features + 1)
          continue
      if self._keep_only_positives_gt:
        if len(example.features.feature[
            'image/object/bbox/xmin'
            ].float_list.value) < 1:
          example.features.feature[
              'context_features_idx'].int64_list.value.append(
                  self._max_num_elements_in_context_features + 1)
          continue

      example_embedding = list(example.features.feature[
          'image/embedding'].float_list.value)
      context_features.extend(example_embedding)
      num_embeddings = example.features.feature[
          'image/embedding_count'].int64_list.value[0]
      example_image_id = example.features.feature[
          'image/source_id'].bytes_list.value[0]
      for _ in range(num_embeddings):
        example.features.feature[
            'context_features_idx'].int64_list.value.append(count)
        count += 1
        context_features_image_id_list.append(example_image_id)

    if not example_embedding:
      example_embedding.append(np.zeros(self._context_feature_length))

    feature_length = self._context_feature_length

    # If the example_list is not empty and image/embedding_length is in the
    # featture dict, feature_length will be assigned to that. Otherwise, it will
    # be kept as default.
    if example_list and (
        'image/embedding_length' in example_list[0].features.feature):
      feature_length = example_list[0].features.feature[
          'image/embedding_length'].int64_list.value[0]

    if self._pad_context_features:
      while len(context_features_image_id_list) < (
          self._max_num_elements_in_context_features):
        context_features_image_id_list.append('')

    return context_features, feature_length, context_features_image_id_list