def validate_flags(flags_obj: flags.FlagValues,
                   file_exists_fn: Callable[[str], bool]):
  """Raises ValueError if any flags are misconfigured.

  Args:
    flags_obj: A `flags.FlagValues` object, usually from `flags.FLAG`.
    file_exists_fn: A callable to decide if a file path exists or not.
  """

  def _check_path_exists(flag_path, flag_name):
    if not file_exists_fn(flag_path):
      raise ValueError('Flag `%s` at %s does not exist.' %
                       (flag_name, flag_path))

  def _validate_path(flag_path, flag_name):
    if not flag_path:
      raise ValueError('Flag `%s` must be provided in mode %s.' %
                       (flag_name, flags_obj.mode))
    _check_path_exists(flag_path, flag_name)

  if 'train' in flags_obj.mode:
    _validate_path(flags_obj.train_input_path, 'train_input_path')
    _validate_path(flags_obj.input_meta_data_path, 'input_meta_data_path')

    if flags_obj.gin_file:
      for gin_file in flags_obj.gin_file:
        _check_path_exists(gin_file, 'gin_file')
    if flags_obj.config_file:
      for config_file in flags_obj.config_file:
        _check_path_exists(config_file, 'config_file')

  if 'eval' in flags_obj.mode:
    _validate_path(flags_obj.validation_input_path, 'validation_input_path')

  if flags_obj.mode == 'predict':
    # model_dir is only needed strictly in 'predict' mode.
    _validate_path(flags_obj.model_dir, 'model_dir')

  if 'predict' in flags_obj.mode:
    _validate_path(flags_obj.test_input_path, 'test_input_path')

  if not flags_obj.config_file and flags_obj.mode != 'predict':
    if flags_obj.hub_module_url:
      if flags_obj.init_checkpoint or flags_obj.model_config_file:
        raise ValueError(
            'When `hub_module_url` is specified, `init_checkpoint` and '
            '`model_config_file` should be empty.')
      logging.info(
          'Using the pretrained tf.hub from %s', flags_obj.hub_module_url)
    else:
      if not (flags_obj.init_checkpoint and flags_obj.model_config_file):
        raise ValueError('Both `init_checkpoint` and `model_config_file` '
                         'should be specified if `config_file` is not '
                         'specified.')
      _validate_path(flags_obj.model_config_file, 'model_config_file')
      logging.info(
          'Using the pretrained checkpoint from %s and model_config_file from '
          '%s.', flags_obj.init_checkpoint, flags_obj.model_config_file)