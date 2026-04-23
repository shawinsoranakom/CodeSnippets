def update_input_reader_config(configs,
                               key_name=None,
                               input_name=None,
                               field_name=None,
                               value=None,
                               path_updater=_update_tf_record_input_path):
  """Updates specified input reader config field.

  Args:
    configs: Dictionary of configuration objects. See outputs from
      get_configs_from_pipeline_file() or get_configs_from_multiple_files().
    key_name: Name of the input config we should update, either
      'train_input_config' or 'eval_input_configs'
    input_name: String name used to identify input config to update with. Should
      be either None or value of the 'name' field in one of the input reader
      configs.
    field_name: Field name in input_reader_pb2.InputReader.
    value: Value used to override existing field value.
    path_updater: helper function used to update the input path. Only used when
      field_name is "input_path".

  Raises:
    ValueError: when input field_name is None.
    ValueError: when input_name is None and number of eval_input_readers does
      not equal to 1.
  """
  if isinstance(configs[key_name], input_reader_pb2.InputReader):
    # Updates singular input_config object.
    target_input_config = configs[key_name]
    if field_name == "input_path":
      path_updater(input_config=target_input_config, input_path=value)
    else:
      setattr(target_input_config, field_name, value)
  elif input_name is None and len(configs[key_name]) == 1:
    # Updates first (and the only) object of input_config list.
    target_input_config = configs[key_name][0]
    if field_name == "input_path":
      path_updater(input_config=target_input_config, input_path=value)
    else:
      setattr(target_input_config, field_name, value)
  elif input_name is not None and len(configs[key_name]):
    # Updates input_config whose name matches input_name.
    update_count = 0
    for input_config in configs[key_name]:
      if input_config.name == input_name:
        setattr(input_config, field_name, value)
        update_count = update_count + 1
    if not update_count:
      raise ValueError(
          "Input name {} not found when overriding.".format(input_name))
    elif update_count > 1:
      raise ValueError("Duplicate input name found when overriding.")
  else:
    key_name = "None" if key_name is None else key_name
    input_name = "None" if input_name is None else input_name
    field_name = "None" if field_name is None else field_name
    raise ValueError("Unknown input config overriding: "
                     "key_name:{}, input_name:{}, field_name:{}.".format(
                         key_name, input_name, field_name))