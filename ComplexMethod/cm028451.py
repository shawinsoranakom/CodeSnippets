def __call__(self, ctx=None, batch_size: int = None):
    """Provides tf.data.Dataset object.

    Args:
      ctx: context object.
      batch_size: expected batch size input data.

    Returns:
      tf.data.Dataset object.
    """
    if not batch_size:
      batch_size = self._batch_size
    assert batch_size is not None
    dataset = tf.data.Dataset.list_files(
        self._file_pattern, shuffle=self._is_training)

    if self._input_sharding and ctx and ctx.num_input_pipelines > 1:
      dataset = dataset.shard(ctx.num_input_pipelines, ctx.input_pipeline_id)
    dataset = dataset.cache()

    if self._is_training:
      dataset = dataset.repeat()

    dataset = dataset.interleave(
        map_func=self._dataset_fn,
        cycle_length=32,
        num_parallel_calls=tf.data.experimental.AUTOTUNE)

    if self._is_training:
      dataset = dataset.shuffle(1000)
    if self._num_examples > 0:
      dataset = dataset.take(self._num_examples)

    # Parses the fetched records to input tensors for model function.
    dataset = dataset.map(
        self._parser_fn, num_parallel_calls=tf.data.experimental.AUTOTUNE)
    dataset = dataset.batch(batch_size, drop_remainder=True)
    dataset = dataset.prefetch(tf.data.experimental.AUTOTUNE)
    return dataset