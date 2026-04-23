def main(_):

  params = exp_factory.get_exp_config(FLAGS.experiment)
  for config_file in FLAGS.config_file or []:
    try:
      params = hyperparams.override_params_dict(
          params, config_file, is_strict=True
      )
    except KeyError:
      params = hyperparams.override_params_dict(
          params, config_file, is_strict=False
      )
  if FLAGS.params_override:
    try:
      params = hyperparams.override_params_dict(
          params, FLAGS.params_override, is_strict=True
      )
    except KeyError:
      params = hyperparams.override_params_dict(
          params, FLAGS.params_override, is_strict=False
      )
  params.validate()
  params.lock()

  input_image_size = [int(x) for x in FLAGS.input_image_size.split(',')]

  export_module = export_module_factory.get_export_module(
      params=params,
      input_type=FLAGS.input_type,
      batch_size=FLAGS.batch_size,
      input_image_size=[int(x) for x in FLAGS.input_image_size.split(',')],
      num_channels=3,
      input_name=_INPUT_NAME.value)

  export_saved_model_lib.export_inference_graph(
      input_type=FLAGS.input_type,
      batch_size=FLAGS.batch_size,
      input_image_size=input_image_size,
      params=params,
      checkpoint_path=FLAGS.checkpoint_path,
      export_dir=FLAGS.export_dir,
      export_module=export_module,
      export_saved_model_subdir=_EXPORT_SAVED_MODEL_SUBDIR.value)