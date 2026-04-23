def check_and_parse_input_config_key(configs, key):
  """Checks key and returns specific fields if key is valid input config update.

  Args:
    configs: Dictionary of configuration objects. See outputs from
      get_configs_from_pipeline_file() or get_configs_from_multiple_files().
    key: string indicates the target of update operation.

  Returns:
    is_valid_input_config_key: A boolean indicate whether the input key is to
      update input config(s).
    key_name: 'eval_input_configs' or 'train_input_config' string if
      is_valid_input_config_key is true. None if is_valid_input_config_key is
      false.
    input_name: the name of the input config to be updated. None if
      is_valid_input_config_key is false.
    field_name: the field name in input config. `key` itself if
      is_valid_input_config_key is false.

  Raises:
    ValueError: when the input key format doesn't match any known formats.
    ValueError: if key_name doesn't match 'eval_input_configs' or
      'train_input_config'.
    ValueError: if input_name doesn't match any name in train or eval input
      configs.
    ValueError: if field_name doesn't match any supported fields.
  """
  key_name = None
  input_name = None
  field_name = None
  fields = key.split(":")
  if len(fields) == 1:
    field_name = key
    return _check_and_convert_legacy_input_config_key(key)
  elif len(fields) == 3:
    key_name = fields[0]
    input_name = fields[1]
    field_name = fields[2]
  else:
    raise ValueError("Invalid key format when overriding configs.")

  # Checks if key_name is valid for specific update.
  if key_name not in ["eval_input_configs", "train_input_config"]:
    raise ValueError("Invalid key_name when overriding input config.")

  # Checks if input_name is valid for specific update. For train input config it
  # should match configs[key_name].name, for eval input configs it should match
  # the name field of one of the eval_input_configs.
  if isinstance(configs[key_name], input_reader_pb2.InputReader):
    is_valid_input_name = configs[key_name].name == input_name
  else:
    is_valid_input_name = input_name in [
        eval_input_config.name for eval_input_config in configs[key_name]
    ]
  if not is_valid_input_name:
    raise ValueError("Invalid input_name when overriding input config.")

  # Checks if field_name is valid for specific update.
  if field_name not in [
      "input_path", "label_map_path", "shuffle", "mask_type",
      "sample_1_of_n_examples"
  ]:
    raise ValueError("Invalid field_name when overriding input config.")

  return True, key_name, input_name, field_name