def pipeline(self, dataset: tf.data.Dataset) -> tf.data.Dataset:
    """Build a pipeline fetching, shuffling, and preprocessing the dataset.

    Args:
      dataset: A `tf.data.Dataset` that loads raw files.

    Returns:
      A TensorFlow dataset outputting batched images and labels.
    """
    if (self.config.builder != 'tfds' and self.input_context and
        self.input_context.num_input_pipelines > 1):
      dataset = dataset.shard(self.input_context.num_input_pipelines,
                              self.input_context.input_pipeline_id)
      logging.info(
          'Sharding the dataset: input_pipeline_id=%d '
          'num_input_pipelines=%d', self.input_context.num_input_pipelines,
          self.input_context.input_pipeline_id)

    if self.is_training and self.config.builder == 'records':
      # Shuffle the input files.
      dataset.shuffle(buffer_size=self.config.file_shuffle_buffer_size)

    if self.is_training and not self.config.cache:
      dataset = dataset.repeat()

    if self.config.builder == 'records':
      # Read the data from disk in parallel
      dataset = dataset.interleave(
          tf.data.TFRecordDataset,
          cycle_length=10,
          block_length=1,
          num_parallel_calls=tf.data.experimental.AUTOTUNE)

    if self.config.cache:
      dataset = dataset.cache()

    if self.is_training:
      dataset = dataset.shuffle(self.config.shuffle_buffer_size)
      dataset = dataset.repeat()

    # Parse, pre-process, and batch the data in parallel
    if self.config.builder == 'records':
      preprocess = self.parse_record
    else:
      preprocess = self.preprocess
    dataset = dataset.map(
        preprocess, num_parallel_calls=tf.data.experimental.AUTOTUNE)

    if self.input_context and self.config.num_devices > 1:
      if not self.config.use_per_replica_batch_size:
        raise ValueError(
            'The builder does not support a global batch size with more than '
            'one replica. Got {} replicas. Please set a '
            '`per_replica_batch_size` and enable '
            '`use_per_replica_batch_size=True`.'.format(
                self.config.num_devices))

      # The batch size of the dataset will be multiplied by the number of
      # replicas automatically when strategy.distribute_datasets_from_function
      # is called, so we use local batch size here.
      dataset = dataset.batch(
          self.local_batch_size, drop_remainder=self.is_training)
    else:
      dataset = dataset.batch(
          self.global_batch_size, drop_remainder=self.is_training)

    # Prefetch overlaps in-feed with training
    dataset = dataset.prefetch(tf.data.experimental.AUTOTUNE)

    if self.config.tf_data_service:
      if not hasattr(tf.data.experimental, 'service'):
        raise ValueError('The tf_data_service flag requires Tensorflow version '
                         '>= 2.3.0, but the version is {}'.format(
                             tf.__version__))
      dataset = dataset.apply(
          tf.data.experimental.service.distribute(
              processing_mode='parallel_epochs',
              service=self.config.tf_data_service,
              job_name='resnet_train'))
      dataset = dataset.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)

    return dataset