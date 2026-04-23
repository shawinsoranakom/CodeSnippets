def _shard_files_then_read(matched_files: List[str],
                           dataset_fn,
                           input_context: Optional[
                               tf.distribute.InputContext] = None,
                           seed: Optional[Union[int, tf.Tensor]] = None,
                           is_training: bool = False,
                           sharding: bool = False,
                           cache: bool = False,
                           cycle_length: Optional[int] = None,
                           block_length: Optional[int] = None,
                           deterministic: bool = False) -> tf.data.Dataset:
  """Shards the data files and then sent a split to every worker to read."""
  dataset = tf.data.Dataset.from_tensor_slices(matched_files)

  # Shuffle and repeat at file level.
  # If cache is enabled, `reshuffle_each_iteration` is set to False,
  # because we will read the same cached data in every iteration anyway.
  if is_training:
    # We need a seed to shuffle the files so that when each TPU workers gets
    # its own shard the files do not overlap.
    if sharding and seed is None:
      seed = _get_random_integer()
    dataset = dataset.shuffle(
        len(matched_files),
        seed=seed,
        reshuffle_each_iteration=True if not cache else False)

  # Do not enable sharding if tf.data service is enabled, as sharding will be
  # handled inside tf.data service.
  if sharding and input_context and (input_context.num_input_pipelines > 1):
    dataset = dataset.shard(input_context.num_input_pipelines,
                            input_context.input_pipeline_id)

  # If cache is enabled, we will call `repeat()` later after `cache()`.
  if is_training and not cache:
    dataset = dataset.repeat()

  dataset = dataset.interleave(
      map_func=dataset_fn,
      cycle_length=cycle_length,
      block_length=block_length,
      num_parallel_calls=(cycle_length
                          if cycle_length else tf.data.experimental.AUTOTUNE),
      deterministic=deterministic)
  return dataset