def main(_) -> None:
  params = exp_factory.get_exp_config(_EXPERIMENT.value)
  if _CONFIG_FILE.value is not None:
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

  logging.info('Converting SavedModel from %s to TFLite model...',
               _SAVED_MODEL_DIR.value)

  if _DENYLISTED_OPS.value:
    denylisted_ops = list(_DENYLISTED_OPS.value.split(','))
  else:
    denylisted_ops = None
  tflite_model = export_tflite_lib.convert_tflite_model(
      saved_model_dir=_SAVED_MODEL_DIR.value,
      quant_type=_QUANT_TYPE.value,
      params=params,
      calibration_steps=_CALIBRATION_STEPS.value,
      denylisted_ops=denylisted_ops)

  with tf.io.gfile.GFile(_TFLITE_PATH.value, 'wb') as fw:
    fw.write(tflite_model)

  logging.info('TFLite model converted and saved to %s.', _TFLITE_PATH.value)