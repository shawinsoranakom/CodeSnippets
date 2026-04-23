def merge_external_params_with_configs(configs, hparams=None, kwargs_dict=None):
  """Updates `configs` dictionary based on supplied parameters.

  This utility is for modifying specific fields in the object detection configs.
  Say that one would like to experiment with different learning rates, momentum
  values, or batch sizes. Rather than creating a new config text file for each
  experiment, one can use a single base config file, and update particular
  values.

  There are two types of field overrides:
  1. Strategy-based overrides, which update multiple relevant configuration
  options. For example, updating `learning_rate` will update both the warmup and
  final learning rates.
  In this case key can be one of the following formats:
      1. legacy update: single string that indicates the attribute to be
        updated. E.g. 'label_map_path', 'eval_input_path', 'shuffle'.
        Note that when updating fields (e.g. eval_input_path, eval_shuffle) in
        eval_input_configs, the override will only be applied when
        eval_input_configs has exactly 1 element.
      2. specific update: colon separated string that indicates which field in
        which input_config to update. It should have 3 fields:
        - key_name: Name of the input config we should update, either
          'train_input_config' or 'eval_input_configs'
        - input_name: a 'name' that can be used to identify elements, especially
          when configs[key_name] is a repeated field.
        - field_name: name of the field that you want to override.
        For example, given configs dict as below:
          configs = {
            'model': {...}
            'train_config': {...}
            'train_input_config': {...}
            'eval_config': {...}
            'eval_input_configs': [{ name:"eval_coco", ...},
                                   { name:"eval_voc", ... }]
          }
        Assume we want to update the input_path of the eval_input_config
        whose name is 'eval_coco'. The `key` would then be:
        'eval_input_configs:eval_coco:input_path'
  2. Generic key/value, which update a specific parameter based on namespaced
  configuration keys. For example,
  `model.ssd.loss.hard_example_miner.max_negatives_per_positive` will update the
  hard example miner configuration for an SSD model config. Generic overrides
  are automatically detected based on the namespaced keys.

  Args:
    configs: Dictionary of configuration objects. See outputs from
      get_configs_from_pipeline_file() or get_configs_from_multiple_files().
    hparams: A `HParams`.
    kwargs_dict: Extra keyword arguments that are treated the same way as
      attribute/value pairs in `hparams`. Note that hyperparameters with the
      same names will override keyword arguments.

  Returns:
    `configs` dictionary.

  Raises:
    ValueError: when the key string doesn't match any of its allowed formats.
  """

  if kwargs_dict is None:
    kwargs_dict = {}
  if hparams:
    kwargs_dict.update(hparams.values())
  for key, value in kwargs_dict.items():
    tf.logging.info("Maybe overwriting %s: %s", key, value)
    # pylint: disable=g-explicit-bool-comparison
    if value == "" or value is None:
      continue
    # pylint: enable=g-explicit-bool-comparison
    elif _maybe_update_config_with_key_value(configs, key, value):
      continue
    elif _is_generic_key(key):
      _update_generic(configs, key, value)
    else:
      tf.logging.info("Ignoring config override key: %s", key)
  return configs