def _decode_and_parse_dataset(
      self,
      dataset: Union[tf.data.Dataset, Dict[Text, tf.data.Dataset]],
      batch_size: int,
      input_context: Optional[tf.distribute.InputContext] = None
  ) -> tf.data.Dataset:
    """Returns a tf.data.Dataset object after shuffling, decoding, and parsing."""

    def _shuffle_and_decode(ds):
      # If cache is enabled, we will call `shuffle()` later after `cache()`.
      if self._is_training and not self._cache:
        ds = ds.shuffle(self._shuffle_buffer_size, seed=self._seed)
      # Decode
      ds = _maybe_map_fn(ds, self._decoder_fn)
      return ds

    dataset = tf.nest.map_structure(_shuffle_and_decode, dataset)
    if tf.nest.is_nested(dataset):
      dataset = self._combine_fn(dataset)

    if self._sample_fn is not None:
      dataset = dataset.apply(self._sample_fn)
    dataset = _maybe_map_fn(dataset, self._parser_fn)

    if self._filter_fn is not None:
      dataset = dataset.filter(self._filter_fn)

    if self._cache:
      dataset = dataset.cache()
      if self._is_training:
        dataset = dataset.repeat()
        dataset = dataset.shuffle(self._shuffle_buffer_size, seed=self._seed)

    # Applies tf.data service before batching operations. This is useful when
    # tf.data service is shared between parallel trainers, and batch size is
    # changing between parallel trainers. Then batch size is changing, tf.data
    # services will be considered different instances if applied after batching
    # operations, which make it difficult to share between parallel trainers.
    # However, if there are additional expensive operations in
    # self._transform_and_batch_fn and self._postprocess_fn, the entire tf.data
    # pipeline could be slowed down. In this case, try to move these dataset
    # operations into early stages if possible.
    if (self._enable_shared_tf_data_service_between_parallel_trainers and
        self._apply_tf_data_service_before_batching):
      dataset = self._maybe_apply_data_service(dataset, input_context)

    if self._transform_and_batch_fn is not None:
      dataset = self._transform_and_batch_fn(dataset, input_context)
    else:
      per_replica_batch_size = input_context.get_per_replica_batch_size(
          batch_size) if input_context else batch_size
      dataset = dataset.batch(
          per_replica_batch_size, drop_remainder=self._drop_remainder)

    return dataset