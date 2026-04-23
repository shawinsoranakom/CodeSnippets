def _build_dataset_from_records(self) -> tf.data.Dataset:
    """Build a tf.data.Dataset object from input SSTables.

    If the input data come from multiple SSTables, use the user defined sampling
    weights to perform sampling. For example, if the sampling weights is
    [1., 2.], the second dataset will be sampled twice more often than the first
    one.

    Returns:
      Dataset built from SSTables.
    Raises:
      ValueError for inability to find SSTable files.
    """
    all_file_patterns = []
    if self._use_sampling:
      for file_pattern in self._input_paths:
        all_file_patterns.append([file_pattern])
      # Normalize sampling probabilities.
      total_weight = sum(self._sampling_weights)
      sampling_probabilities = [
          float(w) / total_weight for w in self._sampling_weights
      ]
    else:
      all_file_patterns.append(self._input_paths)

    datasets = []
    for file_pattern in all_file_patterns:
      filenames = sum(list(map(tf.io.gfile.glob, file_pattern)), [])
      if not filenames:
        raise ValueError(
            f'Error trying to read input files for file pattern {file_pattern}')
      # Create a dataset of filenames and shuffle the files. In each epoch,
      # the file order is shuffled again. This may help if
      # per_host_input_for_training = false on TPU.
      dataset = tf.data.Dataset.list_files(
          file_pattern, shuffle=self._is_training)

      if self._is_training:
        dataset = dataset.repeat()

      if self._max_intra_op_parallelism:
        # Disable intra-op parallelism to optimize for throughput instead of
        # latency.
        options = tf.data.Options()
        options.experimental_threading.max_intra_op_parallelism = 1
        dataset = dataset.with_options(options)

      dataset = dataset.interleave(
          self._fetch_dataset,
          cycle_length=self._cycle_length,
          num_parallel_calls=self._cycle_length,
          deterministic=(not self._is_training))

      if self._is_training:
        dataset = dataset.shuffle(self._shuffle_buffer_size)

      datasets.append(dataset)

    if self._use_sampling:
      assert len(datasets) == len(sampling_probabilities)
      dataset = tf.data.experimental.sample_from_datasets(
          datasets, sampling_probabilities)
    else:
      dataset = datasets[0]

    return dataset