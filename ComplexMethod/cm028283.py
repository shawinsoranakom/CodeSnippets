def _sort_image_examples(self, grouped_entry):
    key, example_collection = grouped_entry
    example_list = list(example_collection)

    def get_frame_num(example):
      return example.features.feature['image/seq_frame_num'].int64_list.value[0]

    def get_date_captured(example):
      return datetime.datetime.strptime(
          six.ensure_str(
              example.features.feature[
                  'image/date_captured'].bytes_list.value[0]),
          '%Y-%m-%d %H:%M:%S')

    def get_image_id(example):
      return example.features.feature['image/source_id'].bytes_list.value[0]

    if self._sequence_key == six.ensure_binary('image/seq_id'):
      sorting_fn = get_frame_num
    elif self._sequence_key == six.ensure_binary('image/location'):
      if self._sorted_image_ids:
        sorting_fn = get_image_id
      else:
        sorting_fn = get_date_captured

    sorted_example_list = sorted(example_list, key=sorting_fn)

    num_embeddings = 0
    for example in sorted_example_list:
      num_embeddings += example.features.feature[
          'image/embedding_count'].int64_list.value[0]

    self._num_examples_processed.inc(1)

    # To handle cases where there are more context embeddings within
    # the time horizon than the specified maximum, we split the context group
    # into subsets sequentially in time, with each subset having the maximum
    # number of context embeddings except the final one, which holds the
    # remainder.
    if num_embeddings > self._max_num_elements_in_context_features:
      leftovers = sorted_example_list
      output_list = []
      count = 0
      self._too_many_elements.inc(1)
      num_embeddings = 0
      max_idx = 0
      for idx, example in enumerate(leftovers):
        num_embeddings += example.features.feature[
            'image/embedding_count'].int64_list.value[0]
        if num_embeddings <= self._max_num_elements_in_context_features:
          max_idx = idx
      while num_embeddings > self._max_num_elements_in_context_features:
        self._split_elements.inc(1)
        new_key = key + six.ensure_binary('_' + str(count))
        new_list = leftovers[:max_idx]
        output_list.append((new_key, new_list))
        leftovers = leftovers[max_idx:]
        count += 1
        num_embeddings = 0
        max_idx = 0
        for idx, example in enumerate(leftovers):
          num_embeddings += example.features.feature[
              'image/embedding_count'].int64_list.value[0]
          if num_embeddings <= self._max_num_elements_in_context_features:
            max_idx = idx
      new_key = key + six.ensure_binary('_' + str(count))
      output_list.append((new_key, leftovers))
    else:
      output_list = [(key, sorted_example_list)]

    return output_list