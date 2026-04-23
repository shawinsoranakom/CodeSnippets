def _read_tfds(tfds_name: Text,
               tfds_data_dir: Text,
               tfds_split: Text,
               tfds_skip_decoding_feature: Text,
               tfds_as_supervised: bool,
               input_context: Optional[tf.distribute.InputContext] = None,
               seed: Optional[Union[int, tf.Tensor]] = None,
               is_training: bool = False,
               cache: bool = False,
               cycle_length: Optional[int] = None,
               block_length: Optional[int] = None) -> tf.data.Dataset:
  """Reads a dataset from tfds."""
  repeat_filenames = is_training and not cache
  read_config = tfds.ReadConfig(
      interleave_cycle_length=cycle_length,
      interleave_block_length=block_length,
      input_context=input_context,
      shuffle_seed=seed,
      repeat_filenames=repeat_filenames,
      # Only assert cardinality when we have a finite dataset.
      assert_cardinality=not repeat_filenames,
      skip_prefetch=True)

  decoders = {}
  if tfds_skip_decoding_feature:
    for skip_feature in tfds_skip_decoding_feature.split(','):
      decoders[skip_feature.strip()] = tfds.decode.SkipDecoding()

  if tfds_name.startswith('mldataset.'):
    dataset = tfds.load(name=tfds_name,
                        split=tfds_split,
                        as_supervised=tfds_as_supervised,
                        decoders=decoders if decoders else None,
                        read_config=read_config)
  else:
    builder = tfds.builder(tfds_name, data_dir=tfds_data_dir)
    if builder.info.splits:
      num_shards = len(builder.info.splits[tfds_split].file_instructions)
    else:
      # The tfds mock path often does not provide splits.
      num_shards = 1
    load_kwargs = dict(
        name=tfds_name, download=True, split=tfds_split,
        shuffle_files=is_training, as_supervised=tfds_as_supervised,
        decoders=decoders if decoders else None)
    if tfds_data_dir:
      load_kwargs.update({'data_dir': tfds_data_dir})

    if input_context and num_shards < input_context.num_input_pipelines:
      # The number of files in the dataset split is smaller than the number of
      # input pipelines. We read the entire dataset first and then shard in the
      # host memory.
      read_config = dataclasses.replace(read_config, input_context=None)
      load_kwargs.update({'read_config': read_config})
      dataset = tfds.load(**load_kwargs)
      dataset = dataset.shard(input_context.num_input_pipelines,
                              input_context.input_pipeline_id)
    else:
      load_kwargs.update({'read_config': read_config})
      dataset = tfds.load(**load_kwargs)
  return dataset