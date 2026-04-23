def __init__(
      self,
      params: cfg.DataConfig,
      dataset_fn=tf.data.TFRecordDataset,
      decoder_fn: Optional[Callable[..., Any]] = None,
      combine_fn: Optional[Callable[..., Any]] = None,
      sample_fn: Optional[Callable[..., Any]] = None,
      parser_fn: Optional[Callable[..., Any]] = None,
      filter_fn: Optional[Callable[..., tf.Tensor]] = None,
      transform_and_batch_fn: Optional[
          Callable[
              [tf.data.Dataset, Optional[tf.distribute.InputContext]],
              tf.data.Dataset,
          ]
      ] = None,
      postprocess_fn: Optional[Callable[..., Any]] = None,
  ):
    """Initializes an InputReader instance.

    Args:
      params: A config_definitions.DataConfig object.
      dataset_fn: A `tf.data.Dataset` that consumes the input files. For
        example, it can be `tf.data.TFRecordDataset`.
      decoder_fn: An optional `callable` that takes the serialized data string
        and decodes them into the raw tensor dictionary.
      combine_fn: An optional `callable` that takes a dictionarty of
        `tf.data.Dataset` objects as input and outputs a combined dataset. It
        will be executed after the decoder_fn and before the sample_fn.
      sample_fn: An optional `callable` that takes a `tf.data.Dataset` object as
        input and outputs the transformed dataset. It performs sampling on the
        decoded raw tensors dict before the parser_fn.
      parser_fn: An optional `callable` that takes the decoded raw tensors dict
        and parse them into a dictionary of tensors that can be consumed by the
        model. It will be executed after decoder_fn.
      filter_fn: An optional `callable` mapping a dataset element to a boolean.
        It will be executed after parser_fn.
      transform_and_batch_fn: An optional `callable` that takes a
        `tf.data.Dataset` object and an optional `tf.distribute.InputContext` as
        input, and returns a `tf.data.Dataset` object. It will be executed after
        `parser_fn` to transform and batch the dataset; if None, after
        `parser_fn` is executed, the dataset will be batched into per-replica
        batch size.
      postprocess_fn: A optional `callable` that processes batched tensors. It
        will be executed after batching.
    """
    if params.input_path and params.tfds_name:
      raise ValueError('At most one of `input_path` and `tfds_name` can be '
                       'specified, but got %s and %s.' %
                       (params.input_path, params.tfds_name))

    if (isinstance(params.input_path, cfg.base_config.Config) or
        isinstance(params.tfds_name, cfg.base_config.Config)
        ) and combine_fn is None:
      raise ValueError(
          'A combine_fn is required if `input_path` or `tfds_name` is a dict.')

    self._tfds_name = params.tfds_name
    self._tfds_data_dir = params.tfds_data_dir
    self._matched_files = None
    if not params.input_path:
      # Read dataset from TFDS.
      if not params.tfds_split:
        raise ValueError(
            '`tfds_name` is %s, but `tfds_split` is not specified.' %
            params.tfds_name)
    else:
      self._matched_files = self.get_files(params.input_path)

    self._global_batch_size = params.global_batch_size
    self._is_training = params.is_training
    self._drop_remainder = params.drop_remainder
    self._shuffle_buffer_size = params.shuffle_buffer_size
    self._cache = params.cache
    self._cycle_length = params.cycle_length
    self._block_length = params.block_length
    self._deterministic = params.deterministic
    self._sharding = params.sharding
    self._tfds_split = params.tfds_split
    self._tfds_as_supervised = params.tfds_as_supervised
    self._tfds_skip_decoding_feature = params.tfds_skip_decoding_feature

    self._dataset_fn = dataset_fn
    self._decoder_fn = decoder_fn
    self._combine_fn = combine_fn
    self._sample_fn = sample_fn
    self._parser_fn = parser_fn
    self._transform_and_batch_fn = transform_and_batch_fn
    self._postprocess_fn = postprocess_fn
    self._filter_fn = filter_fn
    self._seed = params.seed
    self._prefetch_buffer_size = (
        params.prefetch_buffer_size or tf.data.experimental.AUTOTUNE)
    self._autotune_algorithm = params.autotune_algorithm
    self._ram_budget = params.ram_budget

    # When tf.data service is enabled, each data service worker should get
    # different random seeds. Thus, we set `seed` to None.
    # Sharding should also be disabled because tf data service handles how
    # each worker shard data with `processing_mode` in distribute method.
    if params.enable_tf_data_service:
      self._seed = None
      self._sharding = False

    self._enable_tf_data_service = (
        params.enable_tf_data_service and params.tf_data_service_address)
    self._tf_data_service_address = params.tf_data_service_address
    self._enable_shared_tf_data_service_between_parallel_trainers = (
        params.enable_shared_tf_data_service_between_parallel_trainers)
    self._apply_tf_data_service_before_batching = (
        params.apply_tf_data_service_before_batching)
    self._trainer_id = params.trainer_id
    if self._enable_tf_data_service:
      # Add a random seed as the tf.data service job name suffix, so tf.data
      # service doesn't reuse the previous state if TPU worker gets preempted.
      # It's necessary to add global batch size into the tf data service job
      # name because when tuning batch size with vizier and tf data service is
      # also enable, the tf data servce job name should be different for
      # different vizier trials since once batch size is changed, from the
      # tf.data perspective, the dataset is a different instance, and a
      # different job name should be used for tf data service. Otherwise, the
      # model would read tensors from the incorrect tf data service job, which
      # would causes dimension mismatch on the batch size dimension.
      self._tf_data_service_job_name = (
          f'{params.tf_data_service_job_name}_bs{params.global_batch_size}_'
          f'{self.static_randnum}')
      self._enable_round_robin_tf_data_service = params.get(
          'enable_round_robin_tf_data_service', False)
      if self._enable_shared_tf_data_service_between_parallel_trainers:
        # When shared tf.data service is enabled, only a single tf.data service
        # instance should be created and shared between parallel trainers. If
        # the global batch size is different across trainers,
        # params.apply_tf_data_service_before_batching should be set to true
        # because tf.data service with different batch sizes will be considered
        # separate tf.data service instances.
        self._tf_data_service_job_name = (
            f'{params.tf_data_service_job_name}_{self.static_randnum}')