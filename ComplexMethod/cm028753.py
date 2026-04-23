def _tokenize_bucketize_and_batch(
      self,
      dataset,
      input_context: Optional[tf.distribute.InputContext] = None):
    dataset = dataset.map(
        self._tokenize, num_parallel_calls=tf.data.experimental.AUTOTUNE)

    if self._params.is_training:
      dataset = dataset.filter(self._filter_max_length)
    else:
      dataset = dataset.map(
          self._maybe_truncate,
          num_parallel_calls=tf.data.experimental.AUTOTUNE)

    per_replica_batch_size = input_context.get_per_replica_batch_size(
        self._global_batch_size) if input_context else self._global_batch_size
    if self._static_batch:
      padded_shapes = {}
      for name, _ in dataset.element_spec.items():
        if name == 'unique_id':
          padded_shapes[name] = []
        else:
          padded_shapes[name] = [self._max_seq_length
                                ] if self._static_batch else [None]
      batch_size = per_replica_batch_size
      if self._params.is_training:
        batch_size = int(batch_size // self._max_seq_length)
      dataset = dataset.padded_batch(
          batch_size,
          padded_shapes,
          drop_remainder=True)
    else:
      # Group and batch such that each batch has examples of similar length.
      dataset = _batch_examples(dataset, per_replica_batch_size,
                                self._max_seq_length)
    # Prefetch the next element to improve speed of input pipeline.
    dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
    return dataset