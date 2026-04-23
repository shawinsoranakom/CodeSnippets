def build(input_reader_config, batch_size=None, transform_input_data_fn=None,
          input_context=None, reduce_to_frame_fn=None):
  """Builds a tf.data.Dataset.

  Builds a tf.data.Dataset by applying the `transform_input_data_fn` on all
  records. Applies a padded batch to the resulting dataset.

  Args:
    input_reader_config: A input_reader_pb2.InputReader object.
    batch_size: Batch size. If batch size is None, no batching is performed.
    transform_input_data_fn: Function to apply transformation to all records,
      or None if no extra decoding is required.
    input_context: optional, A tf.distribute.InputContext object used to
      shard filenames and compute per-replica batch_size when this function
      is being called per-replica.
    reduce_to_frame_fn: Function that extracts frames from tf.SequenceExample
      type input data.

  Returns:
    A tf.data.Dataset based on the input_reader_config.

  Raises:
    ValueError: On invalid input reader proto.
    ValueError: If no input paths are specified.
  """
  if not isinstance(input_reader_config, input_reader_pb2.InputReader):
    raise ValueError('input_reader_config not of type '
                     'input_reader_pb2.InputReader.')

  decoder = decoder_builder.build(input_reader_config)

  if input_reader_config.WhichOneof('input_reader') == 'tf_record_input_reader':
    config = input_reader_config.tf_record_input_reader
    if not config.input_path:
      raise ValueError('At least one input path must be specified in '
                       '`input_reader_config`.')
    def dataset_map_fn(dataset, fn_to_map, batch_size=None,
                       input_reader_config=None):
      """Handles whether or not to use the legacy map function.

      Args:
        dataset: A tf.Dataset.
        fn_to_map: The function to be mapped for that dataset.
        batch_size: Batch size. If batch size is None, no batching is performed.
        input_reader_config: A input_reader_pb2.InputReader object.

      Returns:
        A tf.data.Dataset mapped with fn_to_map.
      """
      if hasattr(dataset, 'map_with_legacy_function'):
        if batch_size:
          num_parallel_calls = batch_size * (
              input_reader_config.num_parallel_batches)
        else:
          num_parallel_calls = input_reader_config.num_parallel_map_calls
        dataset = dataset.map_with_legacy_function(
            fn_to_map, num_parallel_calls=num_parallel_calls)
      else:
        dataset = dataset.map(fn_to_map, tf.data.experimental.AUTOTUNE)
      return dataset
    shard_fn = shard_function_for_context(input_context)
    if input_context is not None:
      batch_size = input_context.get_per_replica_batch_size(batch_size)
    dataset = read_dataset(
        functools.partial(tf.data.TFRecordDataset, buffer_size=8 * 1000 * 1000),
        config.input_path[:], input_reader_config, filename_shard_fn=shard_fn)
    if input_reader_config.sample_1_of_n_examples > 1:
      dataset = dataset.shard(input_reader_config.sample_1_of_n_examples, 0)
    # TODO(rathodv): make batch size a required argument once the old binaries
    # are deleted.
    dataset = dataset_map_fn(dataset, decoder.decode, batch_size,
                             input_reader_config)
    if reduce_to_frame_fn:
      dataset = reduce_to_frame_fn(dataset, dataset_map_fn, batch_size,
                                   input_reader_config)
    if transform_input_data_fn is not None:
      dataset = dataset_map_fn(dataset, transform_input_data_fn,
                               batch_size, input_reader_config)
    if batch_size:
      dataset = dataset.batch(batch_size,
                              drop_remainder=input_reader_config.drop_remainder)
    dataset = dataset.prefetch(input_reader_config.num_prefetch_batches)
    return dataset

  raise ValueError('Unsupported input_reader_config.')