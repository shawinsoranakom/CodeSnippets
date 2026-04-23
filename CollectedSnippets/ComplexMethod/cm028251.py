def _read_dataset_internal(file_read_func,
                           input_files,
                           num_readers,
                           config,
                           filename_shard_fn=None):
  """Reads a dataset, and handles repetition and shuffling.

  Args:
    file_read_func: Function to use in tf_data.parallel_interleave, to read
      every individual file into a tf.data.Dataset.
    input_files: A list of file paths to read.
    num_readers: Number of readers to use.
    config: A input_reader_builder.InputReader object.
    filename_shard_fn: optional, A function used to shard filenames across
      replicas. This function takes as input a TF dataset of filenames and is
      expected to return its sharded version. It is useful when the dataset is
      being loaded on one of possibly many replicas and we want to evenly shard
      the files between the replicas.

  Returns:
    A tf.data.Dataset of (undecoded) tf-records based on config.

  Raises:
    RuntimeError: If no files are found at the supplied path(s).
  """
  filenames = tf.gfile.Glob(input_files)
  tf.logging.info('Reading record datasets for input file: %s' % input_files)
  tf.logging.info('Number of filenames to read: %s' % len(filenames))
  if not filenames:
    raise RuntimeError('Did not find any input files matching the glob pattern '
                       '{}'.format(input_files))
  if num_readers > len(filenames):
    num_readers = len(filenames)
    tf.logging.warning('num_readers has been reduced to %d to match input file '
                       'shards.' % num_readers)
  filename_dataset = tf.data.Dataset.from_tensor_slices(filenames)
  if config.shuffle:
    filename_dataset = filename_dataset.shuffle(
        config.filenames_shuffle_buffer_size)
  elif num_readers > 1:
    tf.logging.warning('`shuffle` is false, but the input data stream is '
                       'still slightly shuffled since `num_readers` > 1.')
  if filename_shard_fn:
    filename_dataset = filename_shard_fn(filename_dataset)

  filename_dataset = filename_dataset.repeat(config.num_epochs or None)
  records_dataset = filename_dataset.apply(
      tf.data.experimental.parallel_interleave(
          file_read_func,
          cycle_length=num_readers,
          block_length=config.read_block_length,
          sloppy=config.shuffle))
  if config.shuffle:
    records_dataset = records_dataset.shuffle(config.shuffle_buffer_size)
  return records_dataset