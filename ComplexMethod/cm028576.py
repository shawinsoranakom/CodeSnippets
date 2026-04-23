def __init__(self,
               is_training: bool,
               batch_size: Optional[int] = None,
               data_root: str = '',
               input_paths: List[str] = gin.REQUIRED,
               dataset_type: str = 'tfrecord',
               use_sampling: bool = False,
               sampling_weights: Optional[Sequence[Union[int, float]]] = None,
               cycle_length: Optional[int] = 64,
               shuffle_buffer_size: Optional[int] = 512,
               parser_fn: Optional[FuncType] = None,
               parser_num_parallel_calls: Optional[int] = 64,
               max_intra_op_parallelism: Optional[int] = None,
               label_map_proto_path: Optional[str] = None,
               input_filter_fns: Optional[List[FuncType]] = None,
               input_training_filter_fns: Optional[Sequence[FuncType]] = None,
               dense_to_ragged_batch: bool = False,
               data_validator_fn: Optional[Callable[[Sequence[str]],
                                                    None]] = None):
    """Input reader constructor.

    Args:
      is_training: Boolean indicating TRAIN or EVAL.
      batch_size: Input data batch size. Ignored if batch size is passed through
        params. In that case, this can be None.
      data_root: All the relative input paths are based on this location.
      input_paths: Input file patterns.
      dataset_type: Can be 'sstable' or 'tfrecord'.
      use_sampling: Whether to perform weighted sampling between different
        datasets.
      sampling_weights: Unnormalized sampling weights. The length should be
        equal to `input_paths`.
      cycle_length: The number of input Datasets to interleave from in parallel.
        If set to None tf.data experimental autotuning is used.
      shuffle_buffer_size: The random shuffle buffer size.
      parser_fn: The function to run decoding and data augmentation. The
        function takes `is_training` as an input, which is passed from here.
      parser_num_parallel_calls: The number of parallel calls for `parser_fn`.
        The number of CPU cores is the suggested value. If set to None tf.data
        experimental autotuning is used.
      max_intra_op_parallelism: if set limits the max intra op parallelism of
        functions run on slices of the input.
      label_map_proto_path: Path to a StringIntLabelMap which will be used to
        decode the input data.
      input_filter_fns: A list of functions on the dataset points which returns
        true for valid data.
      input_training_filter_fns: A list of functions on the dataset points which
        returns true for valid data used only for training.
      dense_to_ragged_batch: Whether to use ragged batching for MPNN format.
      data_validator_fn: If not None, used to validate the data specified by
        input_paths.

    Raises:
      ValueError for invalid input_paths.
    """
    self._is_training = is_training

    if data_root:
      # If an input path is absolute this does not change it.
      input_paths = [os.path.join(data_root, value) for value in input_paths]

    self._input_paths = input_paths
    # Disables datasets sampling during eval.
    self._batch_size = batch_size
    if is_training:
      self._use_sampling = use_sampling
    else:
      self._use_sampling = False
    self._sampling_weights = sampling_weights
    self._cycle_length = (cycle_length if cycle_length else tf.data.AUTOTUNE)
    self._shuffle_buffer_size = shuffle_buffer_size
    self._parser_num_parallel_calls = (
        parser_num_parallel_calls
        if parser_num_parallel_calls else tf.data.AUTOTUNE)
    self._max_intra_op_parallelism = max_intra_op_parallelism
    self._label_map_proto_path = label_map_proto_path
    if label_map_proto_path:
      name_to_id = label_map_util.get_label_map_dict(label_map_proto_path)
      self._lookup_str_keys = list(name_to_id.keys())
      self._lookup_int_values = list(name_to_id.values())
    self._parser_fn = parser_fn
    self._input_filter_fns = input_filter_fns or []
    if is_training and input_training_filter_fns:
      self._input_filter_fns.extend(input_training_filter_fns)
    self._dataset_type = dataset_type
    self._dense_to_ragged_batch = dense_to_ragged_batch

    if data_validator_fn is not None:
      data_validator_fn(self._input_paths)