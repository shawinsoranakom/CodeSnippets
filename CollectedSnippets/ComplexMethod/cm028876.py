def main(_):

  params = exp_factory.get_exp_config(_EXPERIMENT.value)
  for config_file in _CONFIG_FILE.value or []:
    try:
      params = hyperparams.override_params_dict(
          params, config_file, is_strict=True
      )
    except KeyError:
      params = hyperparams.override_params_dict(
          params, config_file, is_strict=False
      )
  if _PARAMS_OVERRIDE.value:
    try:
      params = hyperparams.override_params_dict(
          params, _PARAMS_OVERRIDE.value, is_strict=True
      )
    except KeyError:
      params = hyperparams.override_params_dict(
          params, _PARAMS_OVERRIDE.value, is_strict=False
      )

  params.validate()
  params.lock()

  function_keys = None
  if _FUNCTION_KEYS.value:
    function_keys = {}
    for key_val in _FUNCTION_KEYS.value.split(','):
      key_val_split = key_val.split(':')
      function_keys[key_val_split[0]] = key_val_split[1]

  export_saved_model_lib.export_inference_graph(
      input_type=_IMAGE_TYPE.value,
      batch_size=_BATCH_SIZE.value,
      input_image_size=[int(x) for x in _INPUT_IMAGE_SIZE.value.split(',')],
      params=params,
      checkpoint_path=_CHECKPOINT_PATH.value,
      export_dir=_EXPORT_DIR.value,
      function_keys=function_keys,
      export_checkpoint_subdir=_EXPORT_CHECKPOINT_SUBDIR.value,
      export_saved_model_subdir=_EXPORT_SAVED_MODEL_SUBDIR.value,
      log_model_flops_and_params=_LOG_MODEL_FLOPS_AND_PARAMS.value,
      input_name=_INPUT_NAME.value,
      add_tpu_function_alias=_ADD_TPU_FUNCTION_ALIAS.value,
  )